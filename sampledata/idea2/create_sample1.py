import sys
import argparse

from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives import asymmetric, serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, ec, utils

import hashlib, base64
# from ecdsa.util import sigencode_der

from pyasn1.codec.der.decoder import decode
from pyasn1.codec.der.encoder import encode

from pkixattest import *


#  .----------------------------------.
#  | Attester                         |
#  | --------                         |
#  | AK Certs                         |
#  | hwmodel="RATS HSM 9000"          |
#  | fipsboot=true                    |
#  | .----------.  .----------------. |
#  | | Key 18   |  | Key 21         | | 
#  | | RSA      |  | ECDH-P256      | |
#  | |          |  | Partition1     | |
#  | '----------'  '----------------' |
#  '----------------------------------'



# Load the RSA and P256 certs

def loadCertFromPemFile(file):
    idx, substrate = pem.readPemBlocksFromFile(
        open(file, "r"), ('-----BEGIN CERTIFICATE-----',
                    '-----END CERTIFICATE-----')
    )
    if not substrate:
        return None
    
    cert, rest = decode(substrate, asn1Spec=rfc5280.Certificate())

    return cert

rsaCert = loadCertFromPemFile('rfc9500_rsa.crt')
p256Cert = loadCertFromPemFile('rfc9500_p256.crt')

with open("rfc9500_rsa.priv", "rb") as key_file:
    rsaPrivkey = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
    )

with open("rfc9500_p256.priv", "rb") as key_file:
    p256Privkey = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
    )


# Extract the SPKIs and pub keys from the RSA and P256 certs

rsaSPKI = rsaCert['tbsCertificate']['subjectPublicKeyInfo']

p256SPKI = p256Cert['tbsCertificate']['subjectPublicKeyInfo']

rsaPubKey = rsaSPKI['subjectPublicKey']
p256PubKey = p256SPKI['subjectPublicKey']



# Construct the Attestation


att = PkixKeyAttestation()
att["version"] = 1


## Create key1
    # SingleKeyAttestation ::= SEQUENCE {
    #     keyDescription KeyDescription,
    #     protectionProps SEQUENCE SIZE (0..MAX) of KeyProtectionClaim,
    #     environment SEQUENCE SIZE (0..MAX) of KeyEnvironmentDescription
    # }
    #
    # KeyDescription ::= SEQUENCE {
    #     spki        [0] SubjectPublicKeyInfo OPTIONAL,
    #     fingerprint [1] Fingerprint OPTIONAL,
    #     keyID       [2] IA5String OPTIONAL,
    #     description [3] UTF8String OPTIONAL
    # }

key1 = SingleKeyAttestation()
key1Description = KeyDescription()

key1Description["spki"] = rsaSPKI

key1Fingerprint = Fingerprint()
algID = rfc5280.AlgorithmIdentifier()
algID['algorithm'] = rfc8017.id_sha256
key1Fingerprint['hashAlg'] = algID
fingerprint = hashlib.sha256(bytes(rsaSPKI['subjectPublicKey']))
key1Fingerprint['value'] = univ.OctetString(fingerprint.digest())
key1Description['fingerprint'] = key1Fingerprint

key1Description["keyID"] = char.IA5String('18')

#key1Description["description"] # -- optional, skipping in this example

key1["keyDescription"] = key1Description

claim = PkixClaim_purpose()
claim['type'] = id_pkixattest_purpose
claim['value'] = PkixClaim_purpose.Value.namedValues['Sign']
key1['protectionClaims'].append(claim)

claim = PkixClaim_extractable()
claim['type'] = id_pkixattest_extractable
claim['value'] = univ.Boolean(True)
key1['protectionClaims'].append(claim)

claim = PkixClaim_neverExtractable()
claim['type'] = id_pkixattest_neverExtractable
claim['value'] = univ.Boolean(False)
key1['protectionClaims'].append(claim)

claim = PkixClaim_imported()
claim['type'] = id_pkixattest_imported
claim['value'] = univ.Boolean(False)
key1['protectionClaims'].append(claim)

# key1['environment']  # -- I'm gonna put nothing for this sample.

print('This contains data:')
print(key1)

att['keys'].append(key1)

print('But this is empty (and no error message)')
print(att['keys'])


# TODO: key2


# Platform claims

# claim = PkixClaim_hwvendor()
# claim['type'] = id_pkixattest_hwvendor
# claim['value'] = char.UTF8String("IETF RATS")
# att['platformClaims'].append(claim)

# claim = PkixClaim_hwvendor()
# claim['type'] = id_pkixattest_hwvendor
# claim['value'] = char.UTF8String("IETF RATS")
# att['platformClaims'].append(claim)

# claim = PkixClaim_hwmodel()
# claim['type'] = id_pkixattest_hwmodel
# claim['value'] = char.UTF8String("RATS HSM 9000")
# att['platformClaims'].append(claim)

# claim = PkixClaim_hwserial()
# claim['type'] = id_pkixattest_hwserial
# claim['value'] = char.UTF8String("1234567")
# att['platformClaims'].append(claim)

# claim = PkixClaim_fipsboot()
# claim['type'] = id_pkixattest_fipsboot
# claim['value'] = univ.Boolean(False)
# att['platformClaims'].append(claim)

# claim = PkixClaim_nonce()
# claim['type'] = id_pkixattest_nonce
# claim['value'] = char.IA5String("987654321")
# att['platformClaims'].append(claim)

# claim = PkixClaim_attestationTime()
# claim['type'] = id_pkixattest_attestationTime
# claim['value'] = useful.GeneralizedTime(useful.UTCTime.fromDateTime(datetime.now()))
# att['platformClaims'].append(claim)


# RSA SignatureBlock
# # Sign with the RSA key

# signature = rsaPrivkey.sign(
#     encode(att),
#     padding.PSS(
#         mgf=padding.MGF1(hashes.SHA256()),
#         salt_length=20
#     ),
#     hashes.SHA256()
# )

# signatureBlock = SignatureBlock()
# certChain = univ.SequenceOf(
#             componentType = rfc5280.Certificate(),
#             subtypeSpec = constraint.ValueSizeConstraint(0, MAX)
#         )
# certChain.append(rsaCert)
# signatureBlock['certChain'] = certChain

# algIDRsaPSS = rfc5280.AlgorithmIdentifier()
# algIDRsaPSS['algorithm'] = rfc8017.id_RSASSA_PSS
# pssParams = rfc8017.RSASSA_PSS_params()
# algIdSha256 = rfc5280.AlgorithmIdentifier().subtype(
#         explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 0))
# algIdSha256['algorithm'] = rfc8017.id_sha256
# pssParams['hashAlgorithm'] = algIdSha256
# maskGenAlgId = rfc5280.AlgorithmIdentifier().subtype(
#         explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 1))
# maskGenAlgId['algorithm'] = rfc8017.id_mgf1
# pssParams['maskGenAlgorithm'] = maskGenAlgId
# # pssParams['saltLength'] = univ.Integer(32) # this seems buggy, and rfc4055.py has a default of 20
# algIDRsaPSS['parameters'] = pssParams

# signatureBlock['signatureAlgorithm'] = algIDRsaPSS
# signatureBlock['signatureValue'] = univ.OctetString(signature)

# kat1['signatures'].append(signatureBlock)


# ECDSA SignatureBlock


# att['signatures'].append(rsa)
# att['signatures'].append(ecdsa)
# print(att)























### Old Code ###

# signatures = univ.SequenceOf(
#                     componentType = SignatureBlock(),
#                     subtypeSpec = constraint.ValueSizeConstraint(0, MAX)
#                 )






# # Construct KAT2 token

# # {
# #  "keyID": "21",
# #  "pubKey": <SPKI>,
# #  "keyFingerprintAlg": AlgorithmID(id-sha256),
# #  "keyFingerprint": 0xc3b2a1,
# #  "purpose": {Decapsulate},
# #  "extractable": true,
# #  "neverExtractable": false,
# #  "imported": true,
# # }

# kat2 = PkixAttestation()
# kat2["version"] = 1

# kat2Claims = SetOfClaims()

# claim = PkixClaim_keyID()
# claim['type'] = id_pkixattest_keyid
# claim['value'] = char.IA5String('21')
# kat2Claims.append(claim)

# claim = PkixClaim_pubKey()
# claim['type'] = id_pkixattest_pubKey
# claim['value'] = p256SPKI
# kat2Claims.append(claim)


# claim = PkixClaim_keyFingerprintAlg()
# claim['type'] = id_pkixattest_keyFingerprintAlg
# algID = rfc5280.AlgorithmIdentifier()
# algID['algorithm'] = rfc8017.id_sha256
# claim['value'] = algID
# kat2Claims.append(claim)

# fingerprint = hashlib.sha256(bytes(p256SPKI['subjectPublicKey']))
# claim = PkixClaim_keyFingerprint()
# claim['type'] = id_pkixattest_keyFingerprint
# claim['value'] = univ.OctetString(fingerprint.digest())
# kat2Claims.append(claim)

# claim = PkixClaim_purpose()
# claim['type'] = id_pkixattest_purpose
# claim['value'] = PkixClaim_purpose.Value.namedValues['Decapsulate']
# kat2Claims.append(claim)

# claim = PkixClaim_extractable()
# claim['type'] = id_pkixattest_extractable
# claim['value'] = univ.Boolean(True)
# kat2Claims.append(claim)

# claim = PkixClaim_neverExtractable()
# claim['type'] = id_pkixattest_neverExtractable
# claim['value'] = univ.Boolean(False)
# kat2Claims.append(claim)

# claim = PkixClaim_imported()
# claim['type'] = id_pkixattest_imported
# claim['value'] = univ.Boolean(True)
# kat2Claims.append(claim)


# kat2['claims'] = kat2Claims
# signatures = univ.SequenceOf(
#                     componentType = SignatureBlock(),
#                     subtypeSpec = constraint.ValueSizeConstraint(0, MAX)
#                 )


# # Sign with the P256 key

# hasher = hashes.Hash(hashes.SHA256())
# hasher.update(encode(kat2Claims))
# digest = hasher.finalize()

# signature = p256Privkey.sign(
#     digest,
#     ec.ECDSA(utils.Prehashed(hashes.SHA256()))
# )


# signatureBlock = SignatureBlock()
# certChain = univ.SequenceOf(
#             componentType = rfc5280.Certificate(),
#             subtypeSpec = constraint.ValueSizeConstraint(0, MAX)
#         )
# certChain.append(p256Cert)
# signatureBlock['certChain'] = certChain

# algIdP256 = p256SPKI['algorithm']


# signatureBlock['signatureAlgorithm'] = algIdP256
# signatureBlock['signatureValue'] = univ.OctetString(signature)

# kat2['signatures'].append(signatureBlock)





# # # Compute signatures

# # Compute RSA signature
# signature = rsaPrivkey.sign(
#     encode(kat1Claims),
#     padding.PSS(
#         mgf=padding.MGF1(hashes.SHA256()),
#         salt_length=20
#     ),
#     hashes.SHA256()
# )

# signatureBlock1 = SignatureBlock()
# certChain = univ.SequenceOf(
#             componentType = rfc5280.Certificate(),
#             subtypeSpec = constraint.ValueSizeConstraint(0, MAX)
#         )
# certChain.append(rsaCert)
# signatureBlock1['certChain'] = certChain

# algIDRsaPSS = rfc5280.AlgorithmIdentifier()
# algIDRsaPSS['algorithm'] = rfc8017.id_RSASSA_PSS
# pssParams = rfc8017.RSASSA_PSS_params()
# algIdSha256 = rfc5280.AlgorithmIdentifier().subtype(
#         explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 0))
# algIdSha256['algorithm'] = rfc8017.id_sha256
# pssParams['hashAlgorithm'] = algIdSha256
# maskGenAlgId = rfc5280.AlgorithmIdentifier().subtype(
#         explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 1))
# maskGenAlgId['algorithm'] = rfc8017.id_mgf1
# pssParams['maskGenAlgorithm'] = maskGenAlgId
# # pssParams['saltLength'] = univ.Integer(32) # this seems buggy, and rfc4055.py has a default of 20
# algIDRsaPSS['parameters'] = pssParams

# signatureBlock1['signatureAlgorithm'] = algIDRsaPSS
# signatureBlock1['signatureValue'] = univ.OctetString(signature)

# pat["signatures"].append(signatureBlock1)

# # Compute P256 signature

# hasher = hashes.Hash(hashes.SHA256())
# hasher.update(encode(patClaims))
# digest = hasher.finalize()

# signature = p256Privkey.sign(
#     digest,
#     ec.ECDSA(utils.Prehashed(hashes.SHA256()))
# )


# signatureBlock2 = SignatureBlock()
# certChain = univ.SequenceOf(
#             componentType = rfc5280.Certificate(),
#             subtypeSpec = constraint.ValueSizeConstraint(0, MAX)
#         )
# certChain.append(p256Cert)
# signatureBlock2['certChain'] = certChain

# algIdP256 = p256SPKI['algorithm']


# signatureBlock2['signatureAlgorithm'] = algIdP256
# signatureBlock2['signatureValue'] = univ.OctetString(signature)

# pat['signatures'].append(signatureBlock2)


# print("Outputting PAT to sample2.txt")
# with open('sample2.txt', 'w') as f:
#     f.write(str(pat))
#     f.write("\n")
#     f.write("\n")
#     f.write("PAT DER Base64:\n")
#     f.write(base64.b64encode(encode(pat)).decode('ascii'))


