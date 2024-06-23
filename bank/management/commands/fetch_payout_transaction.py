from django.core.management.base import BaseCommand
import time
import json
import requests
import os
import pandas as pd
import random
from dotenv import load_dotenv
from bank.utils import find_bank_code, check_bank_info
from django.contrib.auth.models import User
from payout.models import Payout

load_dotenv()


class Command(BaseCommand):
    help = 'Fetch payout transaction to mysql'

    def handle(self, *args, **kwargs):

        while True:
            df = pd.read_csv('a.csv', dtype={'accountno': str})
            list_user = User.objects.filter(is_superuser=False)
            df['bank_code'] = df['bankname'].apply(find_bank_code)
            df_new = df.iloc[:5]
            for index, row in df_new.iterrows():
                validated = check_bank_info(row)
                if validated:
                    random_user = random.choice(list(list_user))
                    new_payout = Payout.objects.create(
                        user=random_user,
                        did=row['did'],
                        scode=row['scode'],
                        orderno=row['orderno'],
                        orderid=row['orderid'],
                        money=row['money'],
                        bankname=row['bankname'],
                        accountno=row['accountno'],
                        accountname=row['accountname'],
                        bankcode=row['bank_code'],
                        created_at=row['createtime']
                    )
                    new_payout.save()
            break