import json
import requests


class XRPAPI():

    error = False

    def __init__(self, node: str='http://localhost:3000', api_version: int=1):
        self.node = node
        self.api_version = api_version
        # Check connection and XRP-API server
        try:
            response = requests.get('https://www.google.com/', timeout=2)
        except requests.exceptions.RequestException:
            self.error = True
            self.errorMessage = 'No Internet connection available'
            return
        response = self.ping()
        if 'error' in response:
            self.error = True
            self.errorMessage = f'XRP-API server is not running.\n{response["error"]}'
            return

    def _call(self, endpoint: tuple, payload: dict={},
              headers: dict={}, method: str='GET') -> dict:

        url = f'{self.node}/v{self.api_version}/' + '/'.join(endpoint)

        try:
            if method is 'GET':
                response = requests.get(url, json=payload, headers=headers)
            elif method is 'POST':
                response = requests.post(url, json=payload, headers=headers)
            else:
                raise ValueError('Bad request method')

            status = 'ok' if response.ok else 'error'
            response = response.json()
            response['status'] = status
            return response

        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'error': e}
        except json.JSONDecodeError:
            if response.content == b'':
                return {'status': 'ok', 'message': 'No content'}
            else:
                return {'status': 'error', 'error': 'JSONDecodeError'}

    # Query methods
    def get_account_transactions(self, address: str, ledger_index: int=-1) -> dict:
        '''Get a selection of transactions that affected the specified account.'''
        endpoint = ('accounts', address, 'transactions')
        headers = {} if ledger_index == -1 else {'ledger_index': str(ledger_index)}
        return self._call(endpoint=endpoint, headers=headers)

    def get_account_info(self, address: str, ledger_index: int=-1) -> dict:
        '''Get information about an account in the XRP Ledger. This includes its
        settings, activity, and XRP balance. It also includes the sequence number
        of the next valid transaction for this account, which you should use to
        prepare a transaction from this account. By default, this method returns
        data from the 'current' (in-progress) ledger, which may change before validation.
        '''
        endpoint = ('accounts', address, 'info')
        headers = {} if ledger_index == -1 else {'ledger_index': str(ledger_index)}
        return self._call(endpoint=endpoint, headers=headers)

    def get_account_settings(self, address: str, ledger_index: int=-1) -> dict:
        '''Get an account's settings. These are the settings that can be modified
        by the user. By default, this method returns data from the 'current'
        (in-progress) ledger, which may change before validation.
        '''
        endpoint = ('accounts', address, 'settings')
        headers = {} if ledger_index == -1 else {'ledger_index': str(ledger_index)}
        return self._call(endpoint=endpoint, headers=headers)

    # Transact methods
    def get_transaction(self, transaction_id: str) -> dict:
        '''Look up the status and details of a transaction. By default, this method
        only returns data from ledger versions that have been validated by consensus.
        '''
        endpoint = ('transactions', transaction_id)
        return self._call(endpoint=endpoint)

    def submit_payment(self, source_address: str, destination_address: str,
                       source_tag: str, destination_tag: str, amount: float,
                       api_key: str, submit: bool=True) -> dict:
        '''Sign a payment transaction and submit it to the XRP Ledger network. The
        sending account must match an account address and secret the XRP-API server
        is configured with.
        '''
        endpoint = ('payments',)
        headers = {'Content-Type': 'application/json',
                   'Authorization': f'Bearer {api_key}'}
        payload = {'payment': {
                                 'source_address': source_address,
                                 'source_amount': {
                                                   'value': str(amount),
                                                   'currency': 'XRP'
                                                  },
                                 'destination_address': destination_address,
                                 'destination_amount': {
                                                        'value': str(amount),
                                                        'currency': 'XRP'
                                                       }
                                },
                   'submit': submit
                   }

        if source_tag:
            payload['payment']['source_tag'] = str(source_tag)
        if destination_tag:
            payload['payment']['desination_tag'] = str(destination_tag)

        return self._call(endpoint, payload, headers, 'POST')

    # Meta methods
    def ping(self):
        '''Ping the server to confirm that it is online.'''
        endpoint = ('ping',)
        return self._call(endpoint=endpoint)

    def get_server_info(self):
        '''Retrieve information about the current status of the XRP-API Server
        and the rippled server(s) it is connected to.
        '''
        endpoint = ('servers', 'info')
        return self._call(endpoint=endpoint)

    def get_api_docs(self):
        ''' Return the API specification this server is using.'''
        endpoint = ('apiDocs',)
        return self._call(endpoint=endpoint)

    @staticmethod
    def get_error_message(response: dict) -> str:
        ''' Get a response error simplified string
        '''
        if response['status'] == 'ok':
            return ''

        messages = []
        if 'message' in response:
            messages.append(response['message'])
        if 'path' in response['errors'][0]:
            messages.append(f"{response['errors'][0]['path']}")
        if 'name' in response['errors'][0]:
            messages.append(f"{response['errors'][0]['name']}")
        if 'message' in response['errors'][0]:
            messages.append(f"{response['errors'][0]['message']}")

        # Ensure quotation mark consistency across errors
        messages = [i.replace('"', "'") for i in messages]
        # Delete  duplicated errors
        messages = list(set(messages))
        return ': '.join(messages)
