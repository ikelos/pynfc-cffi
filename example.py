import binascii
import time

from libnfc import ffi, lib as nfc


class MFReader(object):
    MC_AUTH_A = 0x60
    MC_AUTH_B = 0x61
    MC_READ = 0x30
    MC_WRITE = 0xA0

    def __init__(self):
        mods = [(nfc.NMT_ISO14443A, nfc.NBR_106)]

        self.__modulations = ffi.new("nfc_modulation[" + str(len(mods)) + "]")
        for i in range(len(mods)):
            self.__modulations[i].nmt = mods[i][0]
            self.__modulations[i].nbr = mods[i][1]

    def run(self):
        self.__context = ffi.new("nfc_context**")
        nfc.nfc_init(self.__context)
        # Dereference the context
        self.__context = self.__context[0]

        conn_strings = ffi.new("nfc_connstring[10]")
        devices_found = nfc.nfc_list_devices(self.__context, conn_strings, 10)

        if devices_found >= 1:
            self.__device = nfc.nfc_open(self.__context, conn_strings[0])
            try:
                _ = nfc.nfc_initiator_init(self.__device)
                while True:
                    self._poll_loop()
            finally:
                nfc.nfc_close(self.__device)
        else:
            self.logger.info("NFC Waiting for device.")
            time.sleep(5)

    def _poll_loop(self):
        nt = ffi.new("nfc_target*")
        res = nfc.nfc_initiator_poll_target(self.__device, self.__modulations, len(self.__modulations), 10, 2, nt)
        if res < 0:
            raise IOError("NFC Error whilst polling")
        elif res >= 1:
            uid = None
            if nt.nti.nai.szUidLen in [4, 7]:
                uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(nt.nti.nai.szUidLen)])
            if uid:
                print("CARD UID:", str(binascii.hexlify(bytes(uid, "latin1")), "latin1"))
                self._setup_device()
                data = self.read_card(uid)

    def _setup_device(self):
        """Sets all the NFC device settings for reading from Mifare cards"""
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_ACTIVATE_CRYPTO1, True) < 0:
            raise Exception("Error setting Crypto1 enabled")
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_INFINITE_SELECT, False) < 0:
            raise Exception("Error setting Single Select option")
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_AUTO_ISO14443_4, False) < 0:
            raise Exception("Error setting No Auto ISO14443-A jiggery pokery")
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_HANDLE_PARITY, True) < 0:
            raise Exception("Error setting Easy Framing property")

    def select_card(self):
        """Selects a card after a failed authentication attempt (aborted communications)

           Returns the UID of the card selected
        """
        nt = ffi.new("nfc_target*")
        _ = nfc.nfc_initiator_select_passive_target(self.__device, self.__modulations[0], ffi.NULL, 0, nt)
        uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(nt.nti.nai.szUidLen)])
        return uid

    def _authenticate(self, block, uid, key = "\xff\xff\xff\xff\xff\xff", use_b_key = False):
        """Authenticates to a particular block using a specified key"""
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_EASY_FRAMING, True) < 0:
            raise Exception("Error setting Easy Framing property")
        abttx = ffi.new("uint8_t[12]")
        abttx[0] = self.MC_AUTH_A if not use_b_key else self.MC_AUTH_B
        abttx[1] = block
        for i in range(6):
            abttx[i + 2] = ord(key[i])
        for i in range(4):
            abttx[i + 8] = ord(uid[i])
        print("AUTH =>", " ".join([hex(x) for x in abttx]))
        abtrx = ffi.new("uint8_t[250]")
        return nfc.nfc_initiator_transceive_bytes(self.__device, abttx, len(abttx), abtrx, len(abtrx), 0)

    def auth_and_read(self, block, uid, key = "\xff\xff\xff\xff\xff\xff"):
        """Authenticates and then reads a block

           Returns '' if the authentication failed
        """
        # Reselect the card so that we can reauthenticate
        self.select_card()
        res = self._authenticate(block, uid, key)
        print("AUTHRES", res)
        if res >= 0:
            return self._read_block(block)
        return ''

    def _read_block(self, block):
        """Reads a block from a Mifare Card after authentication

           Returns the data read or raises an exception
        """
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_EASY_FRAMING, True) < 0:
            raise Exception("Error setting Easy Framing property")
        abttx = ffi.new("uint8_t[2]")
        abttx[0] = self.MC_READ
        abttx[1] = block
        abtrx = ffi.new("uint8_t[250]")
        print("Read block", hex(abttx[0]), hex(abttx[1]), len(abttx))
        res = nfc.nfc_initiator_transceive_bytes(self.__device, abttx, len(abttx), abtrx, len(abtrx), 0)
        if res < 0:
            raise IOError("Error reading data")
        return "".join([chr(abtrx[i]) for i in range(res)])

    def read_page(self, page):
        self.select_card()
        return self._read_block(page)[:4]

    def read_card(self, uid):
        """Takes a binary uid, reads the card and return data for use in writing the card"""
        data = ""
        for page in range(4, 40, 4):
            data += self._read_block(page)
        print("DATA:", repr(data))


if __name__ == '__main__':
    mf = MFReader()
    mf.run()
