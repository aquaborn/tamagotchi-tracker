// PixelJetton.tact - $PIXEL Token Contract
// Стандартный Jetton с кастомной логикой для игры

import "@stdlib/deploy";
import "@stdlib/ownable";
import "@stdlib/stoppable";

// === Сообщения ===
message Mint {
    amount: Int as coins;
    receiver: Address;
}

message Burn {
    amount: Int as coins;
    response_destination: Address;
}

message TokenTransfer {
    query_id: Int as uint64;
    amount: Int as coins;
    destination: Address;
    response_destination: Address;
    custom_payload: Cell?;
    forward_ton_amount: Int as coins;
    forward_payload: Slice as remaining;
}

message TokenTransferInternal {
    query_id: Int as uint64;
    amount: Int as coins;
    from: Address;
    response_destination: Address;
    forward_ton_amount: Int as coins;
    forward_payload: Slice as remaining;
}

message TokenNotification {
    query_id: Int as uint64;
    amount: Int as coins;
    from: Address;
    forward_payload: Slice as remaining;
}

message TokenBurn {
    query_id: Int as uint64;
    amount: Int as coins;
    response_destination: Address;
    custom_payload: Cell?;
}

message TokenBurnNotification {
    query_id: Int as uint64;
    amount: Int as coins;
    sender: Address;
    response_destination: Address;
}

message TokenExcesses {
    query_id: Int as uint64;
}

message TokenUpdateContent {
    content: Cell;
}

// === JettonData ===
struct JettonData {
    total_supply: Int as coins;
    mintable: Bool;
    admin_address: Address;
    jetton_content: Cell;
    jetton_wallet_code: Cell;
}

// === WalletData ===
struct WalletData {
    balance: Int as coins;
    owner: Address;
    jetton: Address;
    jetton_wallet_code: Cell;
}

// === Pixel Jetton Master ===
contract PixelJettonMaster with Deployable, Ownable, Stoppable {
    total_supply: Int as coins;
    mintable: Bool;
    owner: Address;
    stopped: Bool;
    content: Cell;
    
    // Game-specific
    game_server: Address;  // Адрес который может минтить
    max_supply: Int as coins;
    
    init(owner: Address, content: Cell, game_server: Address) {
        self.total_supply = 0;
        self.mintable = true;
        self.owner = owner;
        self.stopped = false;
        self.content = content;
        self.game_server = game_server;
        self.max_supply = ton("1000000000"); // 1 billion tokens max
    }
    
    // Минтинг (только owner или game_server)
    receive(msg: Mint) {
        let ctx: Context = context();
        require(ctx.sender == self.owner || ctx.sender == self.game_server, "Not authorized");
        require(self.mintable, "Minting disabled");
        require(self.total_supply + msg.amount <= self.max_supply, "Max supply exceeded");
        
        self.total_supply = self.total_supply + msg.amount;
        
        let init: StateInit = self.getJettonWalletInit(msg.receiver);
        send(SendParameters{
            to: contractAddress(init),
            value: 0,
            mode: SendRemainingValue,
            bounce: true,
            body: TokenTransferInternal{
                query_id: 0,
                amount: msg.amount,
                from: myAddress(),
                response_destination: msg.receiver,
                forward_ton_amount: 0,
                forward_payload: emptySlice()
            }.toCell(),
            code: init.code,
            data: init.data
        });
    }
    
    // Сжигание токенов
    receive(msg: TokenBurnNotification) {
        let ctx: Context = context();
        let init: StateInit = self.getJettonWalletInit(msg.sender);
        require(ctx.sender == contractAddress(init), "Invalid sender");
        
        self.total_supply = self.total_supply - msg.amount;
        
        if (msg.response_destination != newAddress(0, 0)) {
            send(SendParameters{
                to: msg.response_destination,
                value: 0,
                mode: SendRemainingValue + SendIgnoreErrors,
                bounce: false,
                body: TokenExcesses{query_id: msg.query_id}.toCell()
            });
        }
    }
    
    // Обновить контент
    receive(msg: TokenUpdateContent) {
        self.requireOwner();
        self.content = msg.content;
    }
    
    // Выключить минтинг навсегда
    receive("stop_mint") {
        self.requireOwner();
        self.mintable = false;
    }
    
    // Установить game server
    receive("set_game_server") {
        self.requireOwner();
        // В реальности нужно передать адрес через сообщение
    }
    
    // === Getters ===
    
    get fun get_jetton_data(): JettonData {
        return JettonData{
            total_supply: self.total_supply,
            mintable: self.mintable,
            admin_address: self.owner,
            jetton_content: self.content,
            jetton_wallet_code: self.getJettonWalletInit(myAddress()).code
        };
    }
    
    get fun get_wallet_address(owner: Address): Address {
        return contractAddress(self.getJettonWalletInit(owner));
    }
    
    get fun getJettonWalletInit(owner: Address): StateInit {
        return initOf PixelJettonWallet(owner, myAddress());
    }
}


// === Pixel Jetton Wallet ===
contract PixelJettonWallet {
    balance: Int as coins;
    owner: Address;
    jetton: Address;
    
    init(owner: Address, jetton: Address) {
        self.balance = 0;
        self.owner = owner;
        self.jetton = jetton;
    }
    
    // Получение токенов
    receive(msg: TokenTransferInternal) {
        let ctx: Context = context();
        
        if (ctx.sender != self.jetton) {
            let init: StateInit = initOf PixelJettonWallet(msg.from, self.jetton);
            require(ctx.sender == contractAddress(init), "Invalid sender");
        }
        
        self.balance = self.balance + msg.amount;
        
        if (msg.forward_ton_amount > 0) {
            send(SendParameters{
                to: self.owner,
                value: msg.forward_ton_amount,
                mode: SendPayGasSeparately,
                bounce: false,
                body: TokenNotification{
                    query_id: msg.query_id,
                    amount: msg.amount,
                    from: msg.from,
                    forward_payload: msg.forward_payload
                }.toCell()
            });
        }
        
        if (msg.response_destination != newAddress(0, 0)) {
            send(SendParameters{
                to: msg.response_destination,
                value: 0,
                mode: SendRemainingValue + SendIgnoreErrors,
                bounce: false,
                body: TokenExcesses{query_id: msg.query_id}.toCell()
            });
        }
    }
    
    // Отправка токенов
    receive(msg: TokenTransfer) {
        let ctx: Context = context();
        require(ctx.sender == self.owner, "Not owner");
        require(self.balance >= msg.amount, "Insufficient balance");
        
        self.balance = self.balance - msg.amount;
        
        let init: StateInit = initOf PixelJettonWallet(msg.destination, self.jetton);
        send(SendParameters{
            to: contractAddress(init),
            value: 0,
            mode: SendRemainingValue,
            bounce: true,
            body: TokenTransferInternal{
                query_id: msg.query_id,
                amount: msg.amount,
                from: self.owner,
                response_destination: msg.response_destination,
                forward_ton_amount: msg.forward_ton_amount,
                forward_payload: msg.forward_payload
            }.toCell(),
            code: init.code,
            data: init.data
        });
    }
    
    // Сжигание токенов
    receive(msg: TokenBurn) {
        let ctx: Context = context();
        require(ctx.sender == self.owner, "Not owner");
        require(self.balance >= msg.amount, "Insufficient balance");
        
        self.balance = self.balance - msg.amount;
        
        send(SendParameters{
            to: self.jetton,
            value: 0,
            mode: SendRemainingValue,
            bounce: true,
            body: TokenBurnNotification{
                query_id: msg.query_id,
                amount: msg.amount,
                sender: self.owner,
                response_destination: msg.response_destination
            }.toCell()
        });
    }
    
    // === Getters ===
    
    get fun get_wallet_data(): WalletData {
        return WalletData{
            balance: self.balance,
            owner: self.owner,
            jetton: self.jetton,
            jetton_wallet_code: initOf PixelJettonWallet(self.owner, self.jetton).code
        };
    }
}
