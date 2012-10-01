
module Filer.Hash where

import Data.ByteString.Lazy.UTF8 (fromString, toString)
import Data.ByteString.Lazy (ByteString, pack, unpack, hGet)
import Data.Hex (hex, unhex)
import Data.Binary (Binary, get, put)


data Hash = Hash ByteString
    deriving Eq, Ord

instance Binary Hash where
    get = liftM Hash get
    put (Hash bytes) = put bytes

hexToBinary :: String -> Maybe ByteString
hexToBinary d = unhex $ fromString $ d

binaryToHex :: ByteString -> String
binaryToHex d = toString $ hex $ d

toHex :: Hash -> String
toHex (Hash bytes) = binaryToHex bytes

fromHex :: String -> Hash
fromHex d = fromMaybe (error "Not a valid hex hash") (maybeFromHex d)

maybeFromHex :: String -> Maybe Hash
maybeFromHex text = do
    b <- hexToBinary text
    maybeFromBinary b

toBinary :: Hash -> ByteString
toBinary (Hash bytes) = bytes

fromBinary :: ByteString -> Hash
fromBinary d = fromMaybe (error "Not a valid binary hash") (maybeFromBinary d) 

maybeFromBinary -> ByteString -> Maybe Hash
maybeFromBinary bytes = if length bytes == hashBinaryLength
    then Just $ Hash d
    else Nothing
    
hashBinaryLength = 32
hashHexLength = hashBinaryLength * 2

readBinaryHash :: Handle -> IO Hash
readBinaryHash handle = do
    bytes <- hGet handle hashBinaryLength
    return $ fromBinary bytes

readHexHash :: Handle -> IO Hash
readHexHash handle = do
    text <- liftM toString $ hGet handle hashHexLength
    return $ fromHex text








