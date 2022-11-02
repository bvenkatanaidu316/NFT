
from pyteal import *

def clear_app():
    return Approve()

def approve_app():
    
    on_create = Seq( [
        App.globalPut(Bytes("owner"), Global.creator_address()),
        Approve(),
    ])

    on_update = Seq(
        Assert(Txn.sender()==App.globalGet(Bytes("owner"))),
        Approve()
    )

    on_delete = Seq(
        Assert(Txn.sender()==App.globalGet(Bytes("owner"))),
        Approve()
    )

    on_optin = Approve()

    on_closeout = Reject()

    nft_transfer = Seq([
        Assert(And(
            Txn.sender() == App.globalGet(Bytes("owner")),
            Global.group_size() == Int(1),
            Txn.rekey_to() == Global.zero_address(),
            Txn.accounts.length() == Int(1),
            Txn.accounts[1] != Global.zero_address(),
            )
        ),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.asset_sender: Global.current_application_address(),
            TxnField.asset_receiver: Txn.accounts[1],
            TxnField.asset_amount: Int(1),
            TxnField.xfer_asset: Txn.assets[0],
        }),
        InnerTxnBuilder.Submit(),
        Approve(),
        ] 
    )

    nft_creation = Seq(
        Assert(
            Txn.sender() == App.globalGet(Bytes("owner")),
        ),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetConfig,
            TxnField.config_asset_total: Int(1),
            TxnField.config_asset_decimals: Int(0),
            TxnField.config_asset_unit_name: Bytes("NFT"),
            TxnField.config_asset_name: Bytes("Pluaris NFT"),
            TxnField.config_asset_url: Txn.application_args[1],
            TxnField.config_asset_manager: Global.current_application_address(),
            TxnField.config_asset_clawback:Global.current_application_address(),
        }),
        InnerTxnBuilder.Submit(), 
        Approve(),
    )

    return Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.UpdateApplication, on_update],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.on_completion() == OnComplete.OptIn,on_optin],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.application_args[0] == Bytes("create_NFT"),nft_creation ],
        [Txn.application_args[0] == Bytes("transfer_NFT"),nft_transfer ],
    )

approve_teal= compileTeal(approve_app(), Mode.Application, version=5)
with open("approve.teal","w") as f:
    f.write(approve_teal)

clear_teal= compileTeal(clear_app(), Mode.Application, version=5)
with open("clear.teal","w") as f:
    f.write(clear_teal)
