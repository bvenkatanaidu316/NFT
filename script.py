
import json
import base64
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk.future.transaction import AssetTransferTxn, wait_for_confirmation
from algosdk.v2client import indexer

# passphrase="develop menu torch front wish stem ski again general where rule castle virus expire suit minimum duty recycle seat chunk advice imitate journey ability calm"
passphrase="polar curtain tenant usual boy hamster arctic design flock ride soul good smoke frown buzz potato outside put either shadow visa rapid holiday absent brain"

# CONNECT TO NETWORK
algod_address = "https://testnet-api.algonode.cloud"
algod_token = ""
algod_client = algod.AlgodClient(algod_token, algod_address)

# PUBLIC KEY
public_key = mnemonic.to_public_key(passphrase)
    
# SECRET KEY
private_key = mnemonic.to_private_key(passphrase)

owner_address = account.address_from_private_key(private_key)

params = algod_client.suggested_params()
# params.flat_fee = True
# params.fee = 1000

print("____________________________________________________________________________________________")
def deploy_contract():
    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 0
    global_bytes = 1
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    with open("approve.teal","r") as f:
        approval_program =f.read()

    with open("clear.teal","r") as f:
        clear_state_program =f.read()
 
    app_response = algod_client.compile(approval_program)
    rej_response = algod_client.compile(clear_state_program)
    

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real
     
    txn = transaction.ApplicationCreateTxn(
        owner_address,
        params,
        on_complete,
        base64.b64decode(app_response["result"]),
        base64.b64decode(rej_response["result"]),
        global_schema,
        local_schema 
        )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    algod_client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(algod_client, tx_id, 4)
        print("TXID: ", tx_id)
        #print("SC Address: ",get_application_address(tx_id))
        print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    # display results
    transaction_response = algod_client.pending_transaction_info(tx_id)
    app_id = transaction_response['application-index']
    Contract_Address = get_application_address(app_id)
    
    print("Created new app-id:", app_id)
    print("SC Address: ", Contract_Address)
    print("____________________________________________________________________________________________")
    
    feeding_contract(Contract_Address)

def feeding_contract(receiver):
    print("My address: {}".format(owner_address))
    account_info = algod_client.account_info(owner_address)
    amount = 1000000
    unsigned_txn = transaction.PaymentTxn(owner_address, params, receiver,amount , None)

    # sign transaction
    signed_txn = unsigned_txn.sign(private_key)

    # submit transaction
    txid = algod_client.send_transaction(signed_txn)
    print("Signed transaction with txID: {}".format(txid))

    # wait for confirmation 
    try:
        confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 4)  
    except Exception as err:
        print(err)
        return

    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))

    print("Starting Account balance: {} in Algos".format(account_info.get('amount') / 1000000))
    print("Amount transfered: {} microAlgos".format(amount))

    account_info = algod_client.account_info(owner_address)
    print("Final Account balance: {} in Algos".format(account_info.get('amount') / 1000000))
    print("____________________________________________________________________________________________")

# create asset by application
def nft_creation( url):
    print("Creator Account: ", owner_address)
    
    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(owner_address,
    params,
    120215137,
    app_args=["create_NFT",url]
    )

    # sign transaction
    signed_txn = txn.sign(private_key)

    try:
        tx_id = signed_txn.transaction.get_txid()
        # send transaction
        tx_id =algod_client.send_transactions([signed_txn])

        # await confirmation
        wait_for_confirmation(algod_client, tx_id)

        # display results
        transaction_response = algod_client.pending_transaction_info(tx_id)
        print("Asset Created to app-id:", transaction_response["txn"]["txn"]["apid"])

    except Exception as err:
        print(err)
    print("____________________________________________________________________________________________")

# Asset Opt_In transaction
def print_asset_holding(account, assetid):
    account_info = algod_client.account_info(account)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1        
        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break

def asset_opt_in(passphrase,asset_id):
    pk = mnemonic.to_public_key(passphrase)
    sk = mnemonic.to_private_key(passphrase)

    print("Opt_In Asset...")

    account_info = algod_client.account_info(pk)
    holding = None
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1
        if (scrutinized_asset['asset-id'] == asset_id):
            holding = True
            break

    if not holding:
        txn = AssetTransferTxn(
            sender=pk,
            sp=params,
            receiver=pk,
            amt=0,
            index=asset_id
        )
        stxn = txn.sign(sk)
        # Send the transaction to the network and retrieve the txid.
        try:
            txid = algod_client.send_transaction(stxn)
            print("Signed transaction with txID: {}".format(txid))
            # Wait for the transaction to be confirmed
            confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
            print("TXID: ", txid)
            print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))

        except Exception as err:
            print(err)
    
    print_asset_holding(pk, asset_id)
    print("____________________________________________________________________________________________")

def nft_transfer(asset_receiver,asset_id):

    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(owner_address,
    params,
    120215137,
    app_args=["transfer_NFT"],
    accounts=[asset_receiver],
    foreign_assets=[asset_id])

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    try:
        algod_client.send_transactions([signed_txn])
        # await confirmation
        wait_for_confirmation(algod_client, tx_id)
    except Exception as err:
        print(err)
    print("transaction success")
    print("____________________________________________________________________________________________")


     
# deploy_contract()

# app_opt_in("extra hungry share oblige water equip slender surround quality jeans harbor liquid trade labor rapid polar length awake deposit pass success soul night absorb river", 119817120)

# nft_creation("url")
# nft_creation("https://textb.org/t/arawinz.pluaris/")

# asset_opt_in(passphrase,asset_id)
# asset_opt_in( "develop menu torch front wish stem ski again general where rule castle virus expire suit minimum duty recycle seat chunk advice imitate journey ability calm", 120215254)

# nft_transfer(Index, asset_receiver,asset_id)
nft_transfer("SVIBHXXDWUFFCDTL2GXVFLFQJJNVA5OYKWRM2SPXY5OPTZTQXE7GCREXBA",120215254)