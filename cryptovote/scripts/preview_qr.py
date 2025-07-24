import qrcode

# Paste the TOTP URI from your verify-email response
totp_uri = "otpauth://totp/CryptoVote:75e4d195862aeada4fd83cc1691fb9917ced7774f957004fcfc7885aa0c31467%40cryptovote?secret=BBLBIXIAHJZC4TDJMH32L7MSADBLCARM&issuer=CryptoVote"

# Generate and preview the QR code
qrcode.make(totp_uri).show()
