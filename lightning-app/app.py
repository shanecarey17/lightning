import logging
import os

from client import LNClient

import util
util.setup()

if __name__ == '__main__':
    cert_path = os.path.expanduser('~/.lnd/tls.cert')

    alice = LNClient(
        name='alice',
        cert_path=cert_path,
        lnd_url='localhost:10001',
        mac_path='../macaroon/alice.macaroon',
        wallet_pass=b'password',
        seed=['above', 'random', 'region', 'problem', 'bulb', 'damp', 'fatal', 'pact', 'stuff', 'spatial', 'huge', 'pave', 'couch', 'vault', 'squirrel', 'pilot', 'drastic', 'loud', 'seek', 'divert', 'mansion', 'scorpion', 'scheme', 'popular']
    )

    bob = LNClient(
        name='bob',
        cert_path=cert_path,
        lnd_url='localhost:10002',
        mac_path='../macaroon/bob.macaroon',
        wallet_pass=b'password',
        seed=['above', 'dove', 'prosper', 'dose', 'play', 'eagle', 'extra', 'vapor', 'cluster', 'equip', 'innocent', 'burden', 'story', 'only', 'belt', 'size', 'vibrant', 'link', 'soccer', 'opera', 'crisp', 'surface', 'inspire', 'corn']
    )

    charlie = LNClient(
        name='charlie',
        cert_path=cert_path,
        lnd_url='localhost:10003',
        mac_path='../macaroon/charlie.macaroon',
        wallet_pass=b'password',
        seed=['above', 'dry', 'parent', 'riot', 'oblige', 'boat', 'beach', 'lake', 'sick', 'car', 'april', 'silly', 'expand', 'eight', 'base', 'obvious', 'wet', 'record', 'list', 'cook', 'garden', 'program', 'drive', 'divorce']
    )

    all_peers = [alice, bob, charlie]
    for peer in all_peers:
        info = peer.get_info()

        wallet_balance = peer.wallet_balance()

        address = peer.new_address().address

        logging.info('%s %s %s %s', peer.name, wallet_balance.total_balance, info.identity_pubkey, address)


        channels = peer.list_channels()
        for chan in channels.channels:
            logging.info('\t%s %s %s', chan.local_balance, chan.remote_balance, chan.remote_pubkey)

    alice.send_coins(addr=bob.new_address().address, value=5000000)
    alice.send_coins(addr=charlie.new_address().address, value=5000000)

    if False:
        p = bob.add_invoice()

        for r in alice.send_payment(p.payment_request, value=100000):
            logging.info(r)

