import qrcode

# Paste the TOTP URI from your verify-email response
totp_uri = "otpauth://totp/CryptoVote:d59c2d76fc9e6b3bd870b9e9735cde85e3decdf7548fc056704753abac822f22%40cryptovote?secret=LC6XYCNDXDLJK2HOJ6JE4YBK6BELDOW3&issuer=CryptoVote"

# Generate and preview the QR code
qrcode.make(totp_uri).show()
