import time
import grpc
import os
import codecs
import logging

import lightning_pb2 as ln
import lightning_pb2_grpc as lnrpc

import walletunlocker_pb2 as walletunlocker
import walletunlocker_pb2_grpc as walletunlockerrpc

import invoices_pb2 as invoices
import invoices_pb2_grpc as invoicesrpc

# Due to updated ECDSA generated tls.cert we need to let gprc know that
# we need to use that cipher suite otherwise there will be a handhsake
# error when we communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

def _send_payment_generator(**kwargs):
    request = ln.SendRequest(**kwargs)
    yield request
    # Magic sleep which tricks the response to the send_payment() method to actually
    # contain data..., STOLEN!
    time.sleep(5)

class LNClient():
    def __init__(self, name=None, cert_path=None, lnd_url=None, mac_path=None, wallet_pass=None, seed=None):
        self.name = name
        self.seed = seed

        cert = open(cert_path, 'rb').read()
        cert_creds = grpc.ssl_channel_credentials(cert)

        macaroon = codecs.encode(open(mac_path, 'rb').read(), 'hex')
        auth_creds = grpc.metadata_call_credentials(lambda ctx, cbk: cbk([('macaroon', macaroon)], None))

        combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)

        self.channel = grpc.secure_channel(lnd_url, combined_creds)

        self.unlocker = walletunlockerrpc.WalletUnlockerStub(self.channel)

        self.lightning = lnrpc.LightningStub(self.channel)

        self.invoices = invoicesrpc.InvoicesStub(self.channel)

        self._unlock(wallet_pass)

    def _unlock(self, wallet_pass):
        try:
            response = self.unlocker.UnlockWallet(walletunlocker.UnlockWalletRequest(wallet_password=wallet_pass))

            time.sleep(5)
        except grpc.RpcError as exc:
            details = exc.details()

            if details == 'wallet not found':
                self._init_wallet(wallet_pass)
            elif details == 'wallet already unlocked, WalletUnlocker service is no longer available':
                return
            else:
                raise Exception('could not unlock wallet') from exc

    def _init_wallet(self, wallet_pass):
        if self.seed is None:
            response = self.unlocker.GenSeed(walletunlocker.GenSeedRequest())

            self.seed = response.cipher_seed_mnemonic

            logging.info('%s %s', self.name, self.seed)

        return self.unlocker.InitWallet(walletunlocker.InitWalletRequest(wallet_password=wallet_pass, cipher_seed_mnemonic=seed))

    def get_info(self):
        return self.lightning.GetInfo(ln.GetInfoRequest())

    def wallet_balance(self):
        return self.lightning.WalletBalance(ln.WalletBalanceRequest())

    def list_channels(self):
        return self.lightning.ListChannels(ln.ListChannelsRequest())

    def send_coins(self, addr, amount):
        return self.lightning.SendCoins(ln.SendCoinsRequest(addr=addr, amount=amount))

    def add_invoice(self, value=0, expiry=3600, memo='', creation_date=int(time.time())):
        return self.lightning.AddInvoice(ln.Invoice(value=value, expiry=expiry, memo=memo, creation_date=creation_date))

    def send_payment(self, payment_request, value=None):
        return self.lightning.SendPayment(_send_payment_generator(payment_request=payment_request, amt=value))

    def describe_graph(self):
        return self.lightning.DescribeGraph(ln.ChannelGraphRequest())

    def connect_peer(self, pubkey, host):
        return self.lightning.ConnectPeer(ln.ConnectPeerRequest(addr=ln.LightningAddress(pubkey=pubkey, host=host)))

    def new_address(self):
        return self.lightning.NewAddress(ln.NewAddressRequest(type=ln.AddressType.NESTED_PUBKEY_HASH))

    def send_coins(self, addr, value):
        return self.lightning.SendCoins(ln.SendCoinsRequest(addr=addr, amount=value))

