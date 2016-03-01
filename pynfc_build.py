from cffi import FFI

ffi = FFI()

# lib = ffi.dlopen('libnfc.so')
# print('Loaded lib {0}'.format(lib))

ffi.set_source("libnfc",
               """ // passed to the real C compiler
                   #include <nfc/nfc-types.h>
                   #include <nfc/nfc.h>
               """,
               libraries = ["nfc"])  # or a list of libraries to link with
# (more arguments like setup.py's Extension class:
# include_dirs=[..], extra_objects=[..], and so on)

f = open("/usr/include/nfc/nfc-types.h")
data = f.read()
f.close()

data = data[data.index("#endif") + len("#endif"): data.index("#  pragma pack()")]
data = data.replace("NFC_BUFSIZE_CONNSTRING", "1024")

ffi.cdef(data + """

void nfc_init(nfc_context **context);
void nfc_exit(nfc_context *context);
int nfc_register_driver(const nfc_driver *driver);

/* NFC Device/Hardware manipulation */
nfc_device *nfc_open(nfc_context *context, const nfc_connstring connstring);
void nfc_close(nfc_device *pnd);
int nfc_abort_command(nfc_device *pnd);
size_t nfc_list_devices(nfc_context *context, nfc_connstring connstrings[], size_t connstrings_len);
int nfc_idle(nfc_device *pnd);

/* NFC initiator: act as "reader" */
int nfc_initiator_init(nfc_device *pnd);
int nfc_initiator_init_secure_element(nfc_device *pnd);
int nfc_initiator_select_passive_target(nfc_device *pnd, const nfc_modulation nm, const uint8_t *pbtInitData, const size_t szInitData, nfc_target *pnt);
int nfc_initiator_list_passive_targets(nfc_device *pnd, const nfc_modulation nm, nfc_target ant[], const size_t szTargets);
int nfc_initiator_poll_target(nfc_device *pnd, const nfc_modulation *pnmTargetTypes, const size_t szTargetTypes, const uint8_t uiPollNr, const uint8_t uiPeriod, nfc_target *pnt);
int nfc_initiator_select_dep_target(nfc_device *pnd, const nfc_dep_mode ndm, const nfc_baud_rate nbr, const nfc_dep_info *pndiInitiator, nfc_target *pnt, const int timeout);
int nfc_initiator_poll_dep_target(nfc_device *pnd, const nfc_dep_mode ndm, const nfc_baud_rate nbr, const nfc_dep_info *pndiInitiator, nfc_target *pnt, const int timeout);
int nfc_initiator_deselect_target(nfc_device *pnd);
int nfc_initiator_transceive_bytes(nfc_device *pnd, const uint8_t *pbtTx, const size_t szTx, uint8_t *pbtRx, const size_t szRx, int timeout);
int nfc_initiator_transceive_bits(nfc_device *pnd, const uint8_t *pbtTx, const size_t szTxBits, const uint8_t *pbtTxPar, uint8_t *pbtRx, const size_t szRx, uint8_t *pbtRxPar);
int nfc_initiator_transceive_bytes_timed(nfc_device *pnd, const uint8_t *pbtTx, const size_t szTx, uint8_t *pbtRx, const size_t szRx, uint32_t *cycles);
int nfc_initiator_transceive_bits_timed(nfc_device *pnd, const uint8_t *pbtTx, const size_t szTxBits, const uint8_t *pbtTxPar, uint8_t *pbtRx, const size_t szRx, uint8_t *pbtRxPar, uint32_t *cycles);
int nfc_initiator_target_is_present(nfc_device *pnd, const nfc_target *pnt);

/* NFC target: act as tag (i.e. MIFARE Classic) or NFC target device. */
int nfc_target_init(nfc_device *pnd, nfc_target *pnt, uint8_t *pbtRx, const size_t szRx, int timeout);
int nfc_target_send_bytes(nfc_device *pnd, const uint8_t *pbtTx, const size_t szTx, int timeout);
int nfc_target_receive_bytes(nfc_device *pnd, uint8_t *pbtRx, const size_t szRx, int timeout);
int nfc_target_send_bits(nfc_device *pnd, const uint8_t *pbtTx, const size_t szTxBits, const uint8_t *pbtTxPar);
int nfc_target_receive_bits(nfc_device *pnd, uint8_t *pbtRx, const size_t szRx, uint8_t *pbtRxPar);

/* Error reporting */
const char *nfc_strerror(const nfc_device *pnd);
int nfc_strerror_r(const nfc_device *pnd, char *buf, size_t buflen);
void nfc_perror(const nfc_device *pnd, const char *s);
int nfc_device_get_last_error(const nfc_device *pnd);

/* Special data accessors */
const char *nfc_device_get_name(nfc_device *pnd);
const char *nfc_device_get_connstring(nfc_device *pnd);
int nfc_device_get_supported_modulation(nfc_device *pnd, const nfc_mode mode,  const nfc_modulation_type **const supported_mt);
int nfc_device_get_supported_baud_rate(nfc_device *pnd, const nfc_modulation_type nmt, const nfc_baud_rate **const supported_br);

/* Properties accessors */
int nfc_device_set_property_int(nfc_device *pnd, const nfc_property property, const int value);
int nfc_device_set_property_bool(nfc_device *pnd, const nfc_property property, const bool bEnable);

/* Misc. functions */
/* void iso14443a_crc(uint8_t *pbtData, size_t szLen, uint8_t *pbtCrc);
void iso14443a_crc_append(uint8_t *pbtData, size_t szLen);
void iso14443b_crc(uint8_t *pbtData, size_t szLen, uint8_t *pbtCrc);
void iso14443b_crc_append(uint8_t *pbtData, size_t szLen);
uint8_t *iso14443a_locate_historical_bytes(uint8_t *pbtAts, size_t szAts, size_t *pszTk); */

void nfc_free(void *p);
const char *nfc_version(void);
int nfc_device_get_information_about(nfc_device *pnd, char **buf);

/* String converter functions */
const char *str_nfc_modulation_type(const nfc_modulation_type nmt);
const char *str_nfc_baud_rate(const nfc_baud_rate nbr);
int str_nfc_target(char **buf, const nfc_target *pnt, bool verbose);
""")

if __name__ == "__main__":
    ffi.compile()
