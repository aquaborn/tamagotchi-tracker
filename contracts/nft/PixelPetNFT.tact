// PixelPetNFT.tact - NFT Collection для питомцев PIXEL PET
// TEP-62 совместимый NFT контракт

import "@stdlib/deploy";
import "@stdlib/ownable";

// === Сообщения NFT ===
message NftMint {
    query_id: Int as uint64;
    item_index: Int as uint64;
    amount: Int as coins;
    content: Cell;
    owner: Address;
}

message NftTransfer {
    query_id: Int as uint64;
    new_owner: Address;
    response_destination: Address;
    custom_payload: Cell?;
    forward_amount: Int as coins;
    forward_payload: Slice as remaining;
}

message NftOwnershipAssigned {
    query_id: Int as uint64;
    prev_owner: Address;
    forward_payload: Slice as remaining;
}

message NftExcesses {
    query_id: Int as uint64;
}

message NftGetStaticData {
    query_id: Int as uint64;
}

message NftReportStaticData {
    query_id: Int as uint64;
    index: Int as uint256;
    collection: Address;
}

message NftDestroy {
    query_id: Int as uint64;
}

// === Royalty Params ===
struct RoyaltyParams {
    numerator: Int as uint16;
    denominator: Int as uint16;
    destination: Address;
}

message GetRoyaltyParams {
    query_id: Int as uint64;
}

message ReportRoyaltyParams {
    query_id: Int as uint64;
    numerator: Int as uint16;
    denominator: Int as uint16;
    destination: Address;
}

// === Collection Data ===
struct CollectionData {
    next_item_index: Int;
    collection_content: Cell;
    owner_address: Address;
}

// === Item Data ===
struct ItemData {
    is_initialized: Bool;
    index: Int;
    collection_address: Address;
    owner_address: Address;
    individual_content: Cell;
}

// === Pixel Pet NFT Collection ===
contract PixelPetCollection with Deployable, Ownable {
    next_item_index: Int as uint64;
    owner: Address;
    collection_content: Cell;
    royalty_params: RoyaltyParams;
    
    // Game integration
    game_server: Address;  // Может минтить NFT
    
    init(owner: Address, content: Cell, royalty_destination: Address, game_server: Address) {
        self.next_item_index = 0;
        self.owner = owner;
        self.collection_content = content;
        self.royalty_params = RoyaltyParams{
            numerator: 50,      // 5% royalty
            denominator: 1000,
            destination: royalty_destination
        };
        self.game_server = game_server;
    }
    
    // Минтинг NFT (только owner или game_server)
    receive(msg: NftMint) {
        let ctx: Context = context();
        require(ctx.sender == self.owner || ctx.sender == self.game_server, "Not authorized");
        
        let nft_init: StateInit = self.getNftItemInit(msg.item_index);
        
        send(SendParameters{
            to: contractAddress(nft_init),
            value: msg.amount,
            mode: SendPayGasSeparately,
            bounce: false,
            body: NftDeploy{
                query_id: msg.query_id,
                owner: msg.owner,
                content: msg.content
            }.toCell(),
            code: nft_init.code,
            data: nft_init.data
        });
        
        self.next_item_index = self.next_item_index + 1;
    }
    
    // Пакетный минт
    receive("batch_mint") {
        // Для пакетного минтинга множества NFT
        self.requireOwner();
    }
    
    // Обновить royalty
    receive("update_royalty") {
        self.requireOwner();
        // В реальности royalty передается через сообщение
    }
    
    // Обновить game server
    receive("update_game_server") {
        self.requireOwner();
    }
    
    // Royalty запрос
    receive(msg: GetRoyaltyParams) {
        send(SendParameters{
            to: sender(),
            value: 0,
            mode: SendRemainingValue,
            bounce: false,
            body: ReportRoyaltyParams{
                query_id: msg.query_id,
                numerator: self.royalty_params.numerator,
                denominator: self.royalty_params.denominator,
                destination: self.royalty_params.destination
            }.toCell()
        });
    }
    
    // === Getters ===
    
    get fun get_collection_data(): CollectionData {
        return CollectionData{
            next_item_index: self.next_item_index,
            collection_content: self.collection_content,
            owner_address: self.owner
        };
    }
    
    get fun get_nft_address_by_index(index: Int): Address {
        return contractAddress(self.getNftItemInit(index));
    }
    
    get fun get_nft_content(index: Int, individual_content: Cell): Cell {
        return individual_content; // В простом случае возвращаем как есть
    }
    
    get fun royalty_params(): RoyaltyParams {
        return self.royalty_params;
    }
    
    get fun getNftItemInit(index: Int): StateInit {
        return initOf PixelPetItem(myAddress(), index);
    }
}


// === Сообщение для деплоя NFT Item ===
message NftDeploy {
    query_id: Int as uint64;
    owner: Address;
    content: Cell;
}


// === Pixel Pet NFT Item ===
contract PixelPetItem {
    collection: Address;
    index: Int as uint64;
    owner: Address;
    content: Cell;
    is_initialized: Bool;
    
    // Pet-specific данные (хранятся в content, но можно дублировать)
    pet_id: Int as uint64;
    rarity: Int as uint8;  // 0-5 для common-mythic
    generation: Int as uint8;
    
    init(collection: Address, index: Int) {
        self.collection = collection;
        self.index = index;
        self.owner = collection;  // Временно, до деплоя
        self.content = emptyCell();
        self.is_initialized = false;
        self.pet_id = 0;
        self.rarity = 0;
        self.generation = 0;
    }
    
    // Деплой (инициализация) NFT
    receive(msg: NftDeploy) {
        require(!self.is_initialized, "Already initialized");
        require(sender() == self.collection, "Not collection");
        
        self.owner = msg.owner;
        self.content = msg.content;
        self.is_initialized = true;
        
        // Парсим pet_id из content (первые 8 байт)
        // В реальности нужен более сложный парсинг
    }
    
    // Трансфер NFT
    receive(msg: NftTransfer) {
        let ctx: Context = context();
        require(ctx.sender == self.owner, "Not owner");
        require(self.is_initialized, "Not initialized");
        
        let prev_owner: Address = self.owner;
        self.owner = msg.new_owner;
        
        // Уведомляем нового владельца
        if (msg.forward_amount > 0) {
            send(SendParameters{
                to: msg.new_owner,
                value: msg.forward_amount,
                mode: SendPayGasSeparately,
                bounce: true,
                body: NftOwnershipAssigned{
                    query_id: msg.query_id,
                    prev_owner: prev_owner,
                    forward_payload: msg.forward_payload
                }.toCell()
            });
        }
        
        // Возвращаем излишки
        if (msg.response_destination != newAddress(0, 0)) {
            send(SendParameters{
                to: msg.response_destination,
                value: 0,
                mode: SendRemainingValue + SendIgnoreErrors,
                bounce: false,
                body: NftExcesses{query_id: msg.query_id}.toCell()
            });
        }
    }
    
    // Запрос статических данных
    receive(msg: NftGetStaticData) {
        send(SendParameters{
            to: sender(),
            value: 0,
            mode: SendRemainingValue,
            bounce: false,
            body: NftReportStaticData{
                query_id: msg.query_id,
                index: self.index,
                collection: self.collection
            }.toCell()
        });
    }
    
    // Уничтожение NFT (burn)
    receive(msg: NftDestroy) {
        require(sender() == self.owner, "Not owner");
        self.owner = newAddress(0, 0);  // Сжигаем
        
        send(SendParameters{
            to: sender(),
            value: 0,
            mode: SendRemainingValue + SendDestroyIfZero,
            bounce: false,
            body: NftExcesses{query_id: msg.query_id}.toCell()
        });
    }
    
    // === Getters ===
    
    get fun get_nft_data(): ItemData {
        return ItemData{
            is_initialized: self.is_initialized,
            index: self.index,
            collection_address: self.collection,
            owner_address: self.owner,
            individual_content: self.content
        };
    }
    
    get fun get_owner(): Address {
        return self.owner;
    }
    
    // Game-specific getters
    get fun get_pet_info(): (Int, Int, Int) {
        return (self.pet_id, self.rarity, self.generation);
    }
}
