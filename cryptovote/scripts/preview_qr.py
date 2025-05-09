import qrcode

# Paste the TOTP URI from your verify-email response
totp_uri = "otpauth://totp/CryptoVote:1375736e17cd84a32e25ea9a71934846b40d7e7187c5598674f019260a358d54%40cryptovote?secret=VG3JEG6MKJD4YEBTAH3KRGTHVGKKYQ7V&issuer=CryptoVote"

# Generate and preview the QR code
qrcode.make(totp_uri).show()
