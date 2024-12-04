---
title: Key Attestation
abbrev: Key Attestation
docname: draft-ounsworth-rats-key-attestation-latest
category: std
consensus: true
submissiontype: IETF

ipr: trust200902
area: "Security"
workgroup: "Remote ATtestation ProcedureS"
keyword: Internet-Draft

stand_alone: yes
pi:
  rfcedstyle: yes
  toc: yes
  tocindent: yes
  sortrefs: yes
  symrefs: yes
  strict: yes
  comments: yes
  inline: yes
  text-list-symbols: o-*+
  compact: yes
  subcompact: yes
  consensus: false

author:
  -
    ins: M. Ounsworth
    name: Mike Ounsworth
    org: Entrust Limited
    abbrev: Entrust
    street: 2500 Solandt Road – Suite 100
    city: Ottawa, Ontario
    country: Canada
    code: K2K 3G5
    email: mike.ounsworth@entrust.com
  - name: Henk Birkholz
   organization: Fraunhofer SIT
   email: henk.birkholz@ietf.contact
  - name: Thomas Fossati
   organization: Linaro
   email: thomas.fossati@linaro.org
  -
    ins: M. Wiseman
    name: Monty Wiseman
    org: Beyond Identity
    country: USA
    email: monty.wiseman@beyondidentity.com
  -
    name: Hannes Tschofenig
    organization: University of Applied Sciences Bonn-Rhein-Sieg
    abbrev: H-BRS
    email: Hannes.Tschofenig@gmx.net

normative:
  RFC2119:
  RFC9334:
  RFC8949:
  I-D.ietf-rats-eat:
  X.680:
     title: "Information technology -- Abstract Syntax Notation One (ASN.1): Specification of basic notation"
     author:
        org: ITU-T
        date: false
     target: https://www.itu.int/rec/T-REC-X.680

informative:
  RFC5912:
  RFC2986:
  RFC4211:
  I-D.bft-rats-kat:
  I-D.ietf-rats-pkix-evidence:
  I-D.ietf-lamps-csr-attestation:
  I-D.fossati-tls-attestation:

entity:
  SELF: "RFCthis"

--- abstract

This document specifies a format for key attestation claims to provide evidence of the security properties of
trusted execution environments and secure elements in which private keys may be generated and stored. This evidence is intended
to be used by a Relying Party, such as a Certification Authority (CA), as part of validating an incoming
certificate signing request (CSR). The specification defines key claims using ASN.1 and CDDL.

--- middle

# Introduction

When a PKI End Entity provides a Certificate Signing Request (CSR) in requesting a certificate from a Certification Authority (CA), 
that entity may wish to provide evidence of the security properties of the hardware security module where
the private key resides. This evidence is verified by a Relying Party, such as a CA, as part of the CSR
validation against a given certificate policy. [{{I-D.ietf-lamps-csr-attestation}}] specifies how to carry
evidence within PKCS#10 [{{RFC2986}}] or Certificate Request Message Format (CRMF) [{{RFC4211}}].

The content and encoding of this evidence in a CSR are not constrained by [{{I-D.ietf-lamps-csr-attestation}}].
Hence, it is possible to use the Entity Attestation Token (EAT) {{I-D.ietf-rats-eat}} or, when a DER-based
encoding of claims is desired, {{I-D.ietf-rats-pkix-evidence}}. For the latter, ASN.1 {{X.680}}{{RFC5912}} is used
to describe the claims, and for EATs the claims are defined in CDDL.

This specification defines the architecture for performing key attestation and registers claims for use with {{I-D.ietf-rats-eat}}
and {{I-D.ietf-rats-pkix-evidence}}.

# Terminology

The following terms are used in this document:

{: vspace="0"}

Root of Trust (RoT):
: A set of software and/or hardware components that need to be trusted
to act as a security foundation required for accomplishing the security
goals of a system. In our case, the RoT is expected to offer the
functionality for attesting to the state of the platform, and to attest
the properties of the identity key (IK). More precisely, it has to atttest
the integrity of the IK (public as well as private key) and the
confidentiality of the IK private key.

Attestation Key (AK):
: Cryptographic key belonging to the RoT that is only used to sign
attestation tokens.

Platform Attestation Key (PAK):
: An AK used specifically for signing attestation tokens relating to the
state of the platform.

Key Attestation:
: Evidence containing properties of the environment(s) in which the private
keys are generated and stored. For example, a Relying Party may want to know whether
a private key is stored in a hardware security module and cannot be
exported in cleartext.

Key Attestation Key (KAK):
: An AK used specifically for signing KATs. In some systems only a
single AK is used. In that case the AK is used as a PAK and a KAK.

Identity Key (IK):
: The IK consists of a private and a public key. The private key is used
by the usage protocol. The public key is included in the Key Attestation
Token.  The IK is protected by the RoT.

Usage Protocol:
: A (security) protocol that requires demonstrating possession of the
private component of the IK.

Attestation Token (AT):
: A collection of claims that a RoT assembles (and signs) with the
purpose of informing - in a verifiable way - relying parties about the
identity and state of the platform. Essentially a type of Evidence as
per the RATS architecture terminology {{RFC9334}}.

Platform Attestation Token (PAT):
: An AT containing claims relating to the security state of the
platform, including software constituting the platform trusted computing
base (TCB). The process of generating a PAT typically involves gathering
data during measured boot.

Key Attestation Token (KAT):
: An AT containing a claim with a public key. The KAT
may also contain other claims, such as those indicating its validity.
The KAT is signed by the KAK. The key attestation service, which is part
of the platform root of trust (RoT), conceptually acts as a local
certification authority since the KAT behaves like a certificate.

Combined Attestation Bundle (CAB):
: A structure used to bundle a KAT and a PAT together for transport in
the usage protocol. If the KAT already includes a PAT, in form of a
nested token, then it already corresponds to a CAB.  A CAB is equivalent
to a certificate that binds the identity of the platform's TCB with the
IK public key.

Presenter:
: Party that proves possession of a private key to a recipient of a KAT.

Recipient:
: Party that receives the KAT containing the proof-of-possession key
information from the presenter.

Key Attestation Service (KAS):
: The issuer that creates the KAT and bundles a KAT together with a PAT
in a CAB.

The reader is assumed to be familiar with the vocabulary and concepts
defined in {{RFC9334}}.

{::boilerplate bcp14-tagged}

# Architecture

Key attestation is an extension to the attestation functionality
described in {{RFC9334}}.  We describe this conceptually by splitting
the internals of the attester into two parts, platform attestation and
key attestation. This split is shown in {{fig-arch}}. These are logical roles
and implementations may combine them into a single physical entity.

Security-sensitive functionality, like attestation, has to be placed
into the Root of Trust (RoT). Since the RoT itself
may be comprised of different components, the design allows platform
attestation to be separated from key attestation whereby platform
attestation is more privileged than the key attestation code.
Cryptographic services, used by key attestation and by platform
attestation, are typically part of separate components within the RoT
but they are not shown in the figure.

The protocol used for communication between the Presenter and the
Recipient is referred as the Usage Protocol. The Usage Protocol, which is
outside the scope of this specification, needs to support
proof-of-possession of the private key (explained further below).
Examples of usage protocols are attested TLS {{I-D.fossati-tls-attestation}}
or attested CSR {{I-D.ietf-lamps-csr-attestation}}.

~~~aasvg
  .------------------------------------.
 | .----------------------------------. |
 | | Attester                         | |
 | | .-------------.  .-------------. | |
 | | | Key         |  | Platform    | | |
 | | | Attestation |  | Attestation | | |
 | | | Service     |  | Service     | | |
 | | '-------------'  '-------------' | |
 | '----------------------------------' |
 |       ^                              |
 |       |       Root of Trust (RoT)    |
  '------+-----------------------------'
         |
         |
         v
 .-----------------.                 .-----------------.
 |                 | Usage Protocol  |                 |
 |    Presenter    +---------------->|    Recipient    |
 |                 |                 |                 |
 '-----------------'                 '-----------------'
~~~
{: #fig-arch title="Architecture"}

The detailed implementations of key attestation may vary but the following
description aims to illustrate one possible approach. The goal of this
algorithm is to demonstrate to the recipient that the sIK (private part
of the IK) has certain security properties. Properties of interest could,
for example, be 'private key is stored in a hardware security model
manufacturered by example.com and cannot be exported in the clear.'.

The process starts with the the Presenter triggering the generation of the IK. The IK consists of a
public key (pIK) and a private key (sIK).  The Presenter may, for
example, use the following API call to trigger the generation of the key
pair for a given algorithm and to obtain a key handle (key_id).

~~~~c
key_id = GenerateKeyPair(alg_id)
~~~~

The private key is created and stored such that it is only accessible to
the KAS rather than to other software layers at the host, such as the
TLS protocol layer i.e. the Presenter.

Next, the KAS needs to trigger the creation of the Platform Attestation
Token (PAT) by the Platform Attestation Service.  The PAT needs to be
linked to the Key Attestation Token (KAT) and this linkage can occur in
a number of ways. One approach is described in this specification in
{{I-D.bft-rats-kat}}. The Key Attestation Token (KAT) includes the public key of
the IK (pIK) and is then signed with the Key Attestation Key (KAK).

To ensure freshness of the PAT and the KAT a nonce is used, as suggested
by the RATS architecture {{RFC9334}}. Here is the symbolic API call
to request a KAT and a PAT, which are concatenated together as the CAB.

~~~~
cab = createCAB(key_id, nonce)
~~~~

Once the CAB has been sent by the Presenter to the Recipient, the
Presenter has to demonstrate possession of the private key.  The
signature operation uses the private key of the IK (sIK).  How this
proof-of-possession of the private key is accomplished depends on the
details of the usage protocol and is outside the scope of this
specification.

The Recipient of the CAB and the proof-of-possession data (such as a
digital signature) first extracts the PAT and the KAT. The PAT and the
KAT may need to be conveyed to a Verifier. If the PAT is in the form of
attestation results the checks can be performed locally at the
Recipient, whereby the following checks are made:

- The signature covering the PAT passes verification when using
  available trust anchor(s).
- The chaining of the PAT and the KAT has to be verified. The detailed
  verification procedure depends on the chaining mechanism utilized.
- The claims in the PAT are matched against stored reference values.
- The signature protecting the KAT must pass verification.
- The KAT is checked for replays.

Once all these steps are completed, the verifier produces the
attestation result and includes (if needed) the IK public key (pIK).

# Key Claims

The following table defines key claims relevant for key attestation:

~~~
| Claim          | OID      | Value        | Section           | Status       |
| -------------- | -------- | ------------ | ----------------- | ------------ |
| KeyId          | TBD      | IA5String    | {{sect-keyid}}    | OPTIONAL     |
| PubKey         | TBD      | OCTET STRING | {{sect-pubkey}}   | RECOMMENDED  |
| Purpose        | TBD      | CHOICE       | {{sect-purpose}}  | RECOMMENDED  |
| NonExportable  | TBD      | BOOLEAN      | {{sect-nonexportable}} | RECOMMENDED |
| Imported       | TBD      | BOOLEAN      | {{sect-imported}} | RECOMMENDED  |
| KeyExpiry      | TBD      | Time         | {{sect-keyexpiry}}| OPTIONAL     |
| FipsBoot       | TBD      | BOOLEAN      | {{sect-fipsboot}} | RECOMMENDED  |
~~~

A Verifier MAY reject an evidence claim if it lacks required information per their
appraisal policy. For example, if a Relying Party mandates a FIPS-certified device,
it SHOULD reject evidence lacking sufficient information to verify the device's FIPS
certification status.

## KeyId {#sect-keyid}

Identifies the subject key, with a vendor-specific format constrained to ASCII (IA5String).

~~~ asn.1
KeyId EVIDENCE-CLAIM ::= IA5String IDENTIFIED BY TBD
~~~

## PubKey {#sect-pubkey}

Represents the subject public key being attested.

~~~ asn.1
PubKey EVIDENCE-CLAIM ::= OCTET STRING IDENTIFIED BY TBD
~~~

## Purpose {#sect-purpose}

Defines the intended usage for the key.

~~~ asn.1
Purpose EVIDENCE-CLAIM ::= CHOICE IDENTIFIED BY TBD {
   Sign, Decrypt, Unwrap, ...
}
~~~

## NonExportable {#sect-nonexportable}

Indicates if the key is non-exportable.

~~~ asn.1
NonExportable EVIDENCE-CLAIM ::= BOOLEAN IDENTIFIED BY TBD
~~~

## Imported {#sect-imported}

Shows whether the key was imported.

~~~ asn.1
Imported EVIDENCE-CLAIM ::= BOOLEAN IDENTIFIED BY TBD
~~~

## KeyExpiry {#sect-keyexpiry}

Defines the expiry date or "not after" time for the key.

~~~ asn.1
KeyExpiry EVIDENCE-CLAIM ::= Time
~~~


## FipsBoot {#sect-fipsboot}

Indicates whether the cryptographic module was booted in a specific FIPS state,
including any required self-tests and conditions specified by its FIPS certificate.

~~~ asn.1
FipsBoot EVIDENCE-CLAIM ::= BOOLEAN IDENTIFIED BY TBD
~~~

> **Note**: "FIPS Boot" alone does not guarantee "FIPS Certification."
This claim should be used alongside a valid FIPS certification.


# Security Considerations {#sec-cons}

TBD.

#  IANA Considerations

Please replace "{{&SELF}}" with the RFC number assigned to this document.

## OID Registration for Key Attestation Claims

This document requests the registration of new Object Identifiers (OIDs) for the key attestation claims defined in this
specification. The OIDs are to be registered under an appropriate OID arc managed by IANA.

The following OIDs are requested:

| Claim Name       | OID      | Reference         |
|-------------------|----------|-------------------|
| `key-id`         | TBD.OID  | {{&SELF}}         |
| `pub-key`        | TBD.OID  | {{&SELF}}         |
| `purpose`        | TBD.OID  | {{&SELF}}         |
| `non-exportable` | TBD.OID  | {{&SELF}}         |
| `imported`       | TBD.OID  | {{&SELF}}         |
| `key-expiry`     | TBD.OID  | {{&SELF}}         |
| `fips-mode`      | TBD.OID  | {{&SELF}}         |
| `vendor-info`    | TBD.OID  | {{&SELF}}         |
| `nested-evidences`| TBD.OID  | {{&SELF}}         |

Note:

- The `TBD.OID` values will be assigned by IANA during the registration process.
- These OIDs are intended for use in ASN.1 data structures for the key attestation claims defined in this document.

## EAT Claims for Key Attestation

This document requests the registration of new claims in the "EAT Claims" registry defined by {{I-D.ietf-rats-eat}}.
These claims are specific to key attestation and are intended for use in the context of the Entity Attestation Token (EAT).

The following claims should be added to the registry:

| Claim Name       | Claim Key | CBOR Type      | Reference         |
|-------------------|-----------|----------------|-------------------|
| `key-id`         | TBD       | tstr           | {{&SELF}}         |
| `pub-key`        | TBD       | bstr           | {{&SELF}}         |
| `purpose`        | TBD       | tstr/array     | {{&SELF}}         |
| `non-exportable` | TBD       | bool           | {{&SELF}}         |
| `imported`       | TBD       | bool           | {{&SELF}}         |
| `key-expiry`     | TBD       | time           | {{&SELF}}         |
| `fips-mode`      | TBD       | bool           | {{&SELF}}         |

Note:

- The exact "Claim Key" values (TBD) will be assigned by IANA during the registration process.
- The CBOR types are defined as per {{RFC8949}}, with appropriate encoding rules for each claim.


--- back

# Acknowledgements

This specification is the work of a design team created by the chairs
of the LAMPS working group. This specification has been developed
based on discussions in that design team.

