class WithdrawalRequest:
    def __init__(self, request_id, user_id, amount, status):
        self.request_id = request_id
        self.user_id = user_id
        self.amount = amount
        self.status = status  # e.g., pending, approved, rejected

    def approve(self):
        self.status = 'approved'

    def reject(self):
        self.status = 'rejected'

class AdminSettings:
    def __init__(self, notification_email, max_daily_withdrawals):
        self.notification_email = notification_email
        self.max_daily_withdrawals = max_daily_withdrawals

    def update_settings(self, notification_email=None, max_daily_withdrawals=None):
        if notification_email:
            self.notification_email = notification_email
        if max_daily_withdrawals:
            self.max_daily_withdrawals = max_daily_withdrawals
