import qrcode

# Paste the TOTP URI from your verify-email response
totp_uri = "otpauth://totp/CryptoVote:f643b216265d3cc6f36f9e847220a1d219c70effd448a261fb998bfcbbaf96f2%40cryptovote?secret=6UEPHLB6R6RMTSVKKF7TLWUJ5QUCX3EJ&issuer=CryptoVote"

# Generate and preview the QR code
qrcode.make(totp_uri).show()
