from celery import shared_task
from .models import *
from django.utils import timezone
from decimal import Decimal
from datetime import datetime


@shared_task
def calculate_interest_accruals():
    today = timezone.now().date()
    loan_accounts = Loan.objects.all()
    for loan in loan_accounts:
        interest_amount = (loan.principal_amount * loan.interest_rate) / 100 / 365  # Daily interest
        accrual = LoanInterestAccrual.objects.create(
            loan_account=loan,
            accrual_date=today,
            interest_amount=interest_amount
        )
        LoanAccountEntry.objects.create(
            loan_account=loan,
            entry_type='interest',
            amount=interest_amount,
            entry_date=today,
            description=f'Interest accrued for {today}',
        )


@shared_task
def process_loan_repayments():
    # Logic to process due repayments
    pass


@shared_task
def handle_repayment_retries():
    # Logic to handle retries for failed repayments
    pass


@shared_task
def apply_penalties_for_missed_repayments():
    today = timezone.now().date()
    # Logic to calculate and apply penalties
    pass


@shared_task
def final_failed_repayment_handling():
    # Logic to handle final failed repayments
    pass


@shared_task
def eod_pd_action_workflow():
    today = datetime.today().date()
    actions = PDNextAction.objects.filter(next_action_date__lte=today, action_status='Pending')

    for action in actions:
        # Perform the next action (e.g., send reminder, apply penalty)
        # Logic to perform the action goes here

        # Update action status to completed
        action.action_status = 'Completed'
        action.save()

        # Update PD Record Status and create the next action if needed
        pd_record = action.pd_record_id
        workflow = PDActionWorkflowConfig.objects.get(current_pd_status=action.current_pd_status)

        # Update PD Record Status
        pd_record.status = workflow.next_pd_status
        pd_record.save()

        # Create next action
        next_action_date = today + timedelta(days=workflow.action_timeline_days)
        PDNextAction.objects.create(
            pd_record_id=pd_record,
            next_action_date=next_action_date,
            next_action_type=workflow.next_action_type,
            current_pd_status=workflow.next_pd_status
        )


@shared_task
def apply_pd_penalties_charges():
    today = datetime.today().date()
    pd_records = PastDueRecord.objects.filter(status='Active')

    for record in pd_records:
        config = PDPenaltiesChargesConfig.objects.filter(charge_trigger__lte=record.days_overdue).first()

        if config:
            penalty = PenaltyAccrual.objects.create(
                pd_record_id=record,
                penalty_amount=config.charge_amount,
                penalty_date=today,
                penalty_type=config.penalty_type,
                status='Applied'
            )

            # Post to Loan Account Receivables
            LoanAccountReceivable.objects.create(
                loan_account_id=record.loan_account_id,
                pd_record_id=record,
                amount_type=config.penalty_type,
                amount_due=config.charge_amount,
                due_date=today,
                status='Due'
            )
