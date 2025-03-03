---
title: PKIX Key Attestation
abbrev: PKIX Key Attestation
docname: draft-ounsworth-rats-pkix-key-attestation-latest

category: std
consensus: true
submissiontype: IETF

ipr: trust200902
area: "Security"
workgroup: "Remote ATtestation procedureS"
keyword: Internet-Draft
coding: utf-8

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
  text-list-symbols: -o*+
  docmapping: yes
  toc_levels: 4

author:
  - name: Mike Ounsworth
    org: Entrust Limited
    abbrev: Entrust
    street: 2500 Solandt Road - Suite 100
    city: Ottawa, Ontario
    country: Canada
    code: K2K 3G5
    email: mike.ounsworth@entrust.com

  - name: Jean-Pierre Fiset
    org: Crypto4A Inc.
    abbrev: Crypto4A
    street: 1550A Laperriere Ave
    city: Ottawa, Ontario
    country: Canada
    code: K1Z 7T2
    email: jp@crypto4a.com

  - name: Hannes Tschofenig
    organization: University of Applied Sciences Bonn-Rhein-Sieg
    abbrev: H-BRS
    country: Germany
    email: Hannes.Tschofenig@gmx.net

  - name: Henk Birkholz
    organization: Fraunhofer SIT
    email: henk.birkholz@ietf.contact

  - name: Monty Wiseman
    org: Beyond Identity
    country: USA
    email: monty.wiseman@beyondidentity.com

  - name: Ned Smith
    organization: Intel Corporation
    country: USA
    email: ned.smith@intel.com

normative:
  RFC2119:
  RFC9334:
  RFC5280:
  I-D.ietf-rats-eat: eat
  X.680:
     title: "Information technology -- Abstract Syntax Notation One (ASN.1): Specification of basic notation"
     author:
        org: ITU-T
        date: false
     target: https://www.itu.int/rec/T-REC-X.680
  X.690:
      title: "Information technology - ASN.1 encoding Rules: Specification of Basic Encoding Rules (BER), Canonical Encoding Rules (CER) and Distinguished Encoding Rules (DER)"
      date: November 2015
      author:
        org: ITU-T
      seriesinfo:
        ISO/IEC: 8825-1:2015
  PKCS11:
    title: "PKCS #11 Specification Version 3.1"
    author:
      name: Dieter Bong, Tony Cox
      org: OASIS PKCS 11 TC
      date: 11 August 2022
    target: https://docs.oasis-open.org/pkcs11/pkcs11-spec/v3.1/cs01/pkcs11-spec-v3.1-cs01.html
  FIPS.140-3:
    -: fips
    title: SECURITY REQUIREMENTS FOR CRYPTOGRAPHIC MODULES
    author:
      org: NIST - Information Technology Laboratory
    seriesinfo:
      FIPS: 140-3
    target: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.140-3.pdf

informative:
  RFC2986:
  RFC6024:
  RFC9019:
  RFC4211:
  I-D.ietf-lamps-csr-attestation:
  I-D.fossati-tls-attestation:
  I-D.ietf-rats-msg-wrap:

entity:
  SELF: "RFCthis"

--- abstract

This document specifies a vendor-agnostic format for attesting to the protection properties of a symmetric or asymmetric cryptographic key within a hardware cryptographic module to support applications such as providing evidence to a Certification Authority that a key is being protected in accordance with the requested certificate profile, or that HSMs can perform key import and maintain the private key protection properties in a robust way even when migrating keys across HSM vendors. This specification includes a format for requesting a key attestation containing certain attributes. This specification is called "PKIX Attestation" because it is designed to be easy to implement on top of a code base that already supports X.509 and PKCS#11 data models.

--- middle

# Introduction

This specification is targeted at attesting to the storage of cryptographic key
material -- symmetric keys or asymmetric private keys -- within a hardware cryptographic
module such as a Hardware Security Module (HSM) or Trusted Platform Module (TPM).
HSMs and TPMs are devices whose primary purpose is to hold cryptographic keys and support interfaces whereby they can be used to perform encrypt, decrypt, sign, MAC and other keyed cryptographic operations on provided data without the key material ever leaving the hardware module.
Typically an HSM or TPM holds an uses cryptographic keys on behalf of an application such as a Certification Authority, a code signing service, a TLS server.
However, also included in the scope of this draft are single-purpose cryptographic devices such as smartcards which may hold only a single application key for a single purpose such as authenticating to a near-field "tap" terminal.
Within this specification we will generically refer to the attesting device as an "HSM", and to the cryptographic keys that it holds an operates on behalf of some other application as "application keys".

The goal of this specification is to provide a standardized format in which an HSM can attest that one or more application keys are contained within a hardware module, and attest to any additional attributes relating to the protection of this key material.

This requires providing evidence to the key protection properties of that key, referred to in
this specification as "key attributes", as well as to the operational state of the hardware platform,
referred to as "platform attributes". This specification also provides a format for requesting that a cryptographic module produce a key attestation about a specific application key, the application keys in a specific sub-environment of the HSM, or that the returned attestation contain a specific set of attributes.
See {{sec-data-model}} for the full information model.


As described below in {{sec-arch}} "Architecture and Conceptual Model", this specification
uses a simplification of the Remote ATtestation procedureS (RATS) Architecture {{RFC9334}}
by assuming that the attesting environment and the target environment
are the same environment, and that this environment only produces evidence as this aligns with the
target hardware platforms. As such, the attestation data format specified in {{sec-data-model}} only contains
evidence (referred to in this document as "attributes") and does not provide for any form of endorsement except for
endorsement of the device's attestation signing key which is endorsed via an X.509 certificate chain rooted
in a trust anchor belonging either to the device manufacturer or to the device operator, as described in {{sec-ak-chain}}.

Unlike other attestation data formats defined by the RATS working group, the format defined in this
document is targeting devices designed to operate within Public Key Infrastructure (PKI) ecosystems;
this motivates the following design choices:

* Attestation data structure defined in ASN.1 {{X.680}} and encoded in Distinguished Encoding Rules (DER) {{X.690}}.
* Endorsement of attesting key uses an X.509 certificate chain {{RFC5280}}.
* Key attributes are mostly just a mapping of the private key properties from PKCS#11 {{PKCS11}}.

For these reasons, this attestation format is called "PKIX Key Attestation" and may be used,
for example within a Certificate Signing Request (CSR) object; {{I-D.ietf-lamps-csr-attestation}} specifies how to carry evidence within PKCS#10 {{RFC2986}} or Certificate Request Message Format (CRMF) {{RFC4211}}.

This document provides a vendor-agnostic format for attesting to the logical and physical protection properties of a cryptographic key and it envisions uses such as providing evidence to a Certification Authority that a key is being protected in accordance with the requested certificate profile, or that HSMs can perform key import and maintain the private key protection properties in a robust way even when migrating keys across HSMs from different vendors.


# Terminology

The reader is assumed to be familiar with the vocabulary and concepts
defined in {{RFC9334}}.

The following terms are used in this document:

{: vspace="0"}

Root of Trust (RoT):
: A set of software and/or hardware components that need to be trusted
to act as a security foundation required for accomplishing the security
goals of a system. In our case, the RoT is expected to offer the
functionality for attesting to the state of the platform, and to attest
the properties of the application key. More precisely, it has to attest
the integrity of the application key (public as well as private key) and the
confidentiality of the private part of the application key. This document makes a simplifying
assumption that the RoT, the attesting environment holding the
attestation key, and the target environment being measured and attested
are all the same environment.

Attestation Key (AK):
: Cryptographic key belonging to the RoT that is only used to sign
attestation tokens.

Hardware Security Module (HSM):
: a physical computing device that safeguards and manages secrets (most importantly cryptographic keys),
and performs encryption, decryption, signing, MACing and other cryptographic operations with the managed
cryptographic keys. HSMs can sometimes host user applications within a secure enclave environment within
the HSM that are often used to extend the cryptographic functionality of the HSM.
This specification takes a broad definition of what counts as an HSM to include smartcards,
USB tokens, and similar devices which this specification refers to as "personal cryptographic tokens",
as well as TPMs, in addition to the usual PCI card, rack-mount, and blade server form-factor
of HSM which this specification refers to as "enterprise-grade" or "cloud-service grade" HSMs.

Key Attestation:
: Evidence containing properties of the environment(s) in which the private
keys are generated and stored. For example, a Relying Party may want to know whether
a private key is stored in a hardware security module and cannot be
exported in cleartext.

Usage Protocol:
: A (security) protocol that requires demonstrating possession of the
private component of the application key.

Attestation Token (AT):
: A collection of claims that a RoT assembles (and signs) with the
purpose of informing - in a verifiable way - relying parties about the
identity and state of the platform. Essentially a type of Evidence as
per the RATS architecture terminology {{RFC9334}}.

Platform Attestation Entity:
: An Entity containing attributes relating to the security state of the
platform,. The process of generating a platform entity typically involves gathering
data during measured boot.

Key Attestation Entity:
: An Entity containing attributes relating to a specific application key
protected by the HSM. The key attestation service is part
of the root of trust (RoT).

Application Key:
: The application key consists of a private and a public key.  The private key is
used by the usage protocol.  The public key is included in the Key
Attestation Token. The Key Attestation Entity makes claims about the
protection of this key.

Trust Anchor:
: As defined in {{RFC6024}} and {{RFC9019}}, a Trust Anchor
"represents an authoritative entity via a public key and
associated data.  The public key is used to verify digital
signatures, and the associated data is used to constrain the types
of information for which the trust anchor is authoritative." The
Trust Anchor may be a certificate, a raw public key, or other
structure, as appropriate.  It can be a non-root certificate when
it is a certificate.

Presenter:
: Party that proves possession of a private key to a recipient of a key
attestation token. Typically this will be an application layer entity,
such as a cryptographiclibrary constructing a Certificate Signing Request
that must embed attestation evidence, or a TLS library attempting to
perform attested TLS. The Presenter is not fulfilling any roles in the
RATS architecture.

Recipient:
: Party that receives the attestation evidence containing the proof-of-possession key
information from the presenter. The Recipient is likely fulfilling
the roles of Verifier and Relying Party in the RATS architecture,
but the exact details of this arrangement is out-of-scope for this
specification.

Key Attestation Service (KAS):
: The module within the HSM that is responsible for parsing the
PKIX Attestation Request, measuring the
Platform and the Key attributes, constructing the PKIX Attestation
object, and signing it with the AK. The KAS fulfills the role of
Attester in the RATS architecture.
Note that real HSMs may or may not implement the Attester as a
single internal module, but this abstraction is used for the
design and security analysis of this specification.

{::boilerplate bcp14-tagged}

# Architecture and Conceptual Model {#sec-arch}

Key attestation is an extension to the attestation functionality
described in {{RFC9334}}. In the general RATS Architecture, an attesting device
consists of a hardware Root of Trust (RoT) which provides the basis for trust in the device,
and then one or more layers of attestations where an attesting environment collects
and signs measurements (evidence) about a target environment. Trust is
established by chaining the cryptographic signatures on each layer of
evidence up to the next layer of attester until the RoT is reached, and trust
is established in the RoT via 3rd party endorsements.
The target devices for this specification tend to operate on a different
architecture and trust model: the devices consist of one single logical environment
(combining the RATS roles of RoT, attesting environment, and target environment together into
a single entity), and trust is established via product validations conducted by third-party
testing labs against standardized security and functional requirements such
as FIPS 140-3 or a given Common Criteria protection profile. A FIPS or CC
certification provided by a testing lab would conceptually count as an
endorsement of the hardware platform in the RATS architecture, but they
are often not digitally-signed
artifacts, and are often conveyed out of band, sometimes via a website or even
via a paper certificate and so they are out of scope for the wire format
specified in this document.

As such, the attestation data format defined in this document does not
capture the full functionality of the RATS architecture. If a device producing
evidence in the specified format requires to also carry nested attestation
statements or endorsements, then it must
be achieved by placing the attestation from this draft within another wrapper
layer such as RATS Conceptual Message Wrapper (CMW) [I-D.ietf-rats-msg-wrap].

~~~aasvg
      .-------------------------------------.
      | Hardware Security Module            |
      |                                     |
      |   Platform environment              |
      |        ^        .-------------.     |
      |        |        | Application |     |
      |        |        | Keys        |     |
      |        |        '-------------'     |
      |        |              ^             |
      |        |              |             |
      |        | measurements |             |
      | .------------------------------.    |
      | | Attestation                  |    |
      | | Service                      |    |
      | '------------------------------'    |
      |     ^    |                          |
      |     |    |                          |
      '-----+----+--------------------------'
Attestation |    | PKIX
    Request |    | Attestation
            |    v
     .-----------------.                 .-----------------.
     |                 | Usage Protocol  |                 |
     |    Presenter    +---------------->|    Recipient    |
     |                 |                 |                 |
     '-----------------'                 '-----------------'
~~~
{: #fig-arch title="Architecture"}

{{fig-arch}} depicts a typical workflow where an external tool queries the HSM
for the status of one or more cryptographic keys that it is protecting ("Application Keys").
The "Presenter" may be, for example, a command-line or graphical user interface which will display
the evidence to an operator or auditor; a cryptographic library which will include
the evidence in a CSR for transmission to a Certification Authority; a TLS library
which will include the evidence in at attested TLS session [I-D.fossati-tls-attestation];
or similar applications, refered to as the "Usage Protocol".

This model does not assume any internal structure or logical separation within the HSM
except for the existence of some kind of attestation service which may or may not be logically separate
from the overall HSM Root of Trust, and that this attestation service measures the
required evidence about both the hardware environment and the application keys
that are being attested.
In addition to emitting key attestation evidence, an HSM may also need to parse it,
for example when running in an operational mode that only allows importing keys
from other HSMs at a comparable security level (requires checking for specific claims) or within the same operational network (requires checking the trust anchor of the attestation key certificate chain).
This implies that the attestation service needs to be
part of the core HSM "kernel" and therefore would be subject to validations such as
FIPS 140-3 or Common Criteria, which motivates a design requirement to keep the evidence
data format as simple as possible and as close as possible to existing functionality
and data models of existing HSM and TPM products.
As such, the information model presented in {{sec-data-model}}
will feel familiar to implementers with experience with PKI and PKCS#11.


## Attestation Key Certificate Chain {#sec-ak-chain}

The data format in this specification represents attestation evidence and
requires third-party endorsement in order to establish trust. Part of this
endorsement is a trust anchor that chains to the HSM's attestation key (AK)
which signs the evidence. In practice the trust anchor will usually be a
manufacturing CA belonging to the device vendor which proves
that the device is genuine and not counterfeit. The trust anchor can also belong
to the device operator as would be the case when the AK certificate is replaced
as part of onboarding the device into a new operational network.

Note that the data format specified in {{sec-data-model}} allows for zero, one, or multiple
'SignatureBlock's, so a single evidence statement could be un-protected, or could be endorsed by multiple
AK chains leading to different trust anchors. See {{sec-verif-proc}} for a discussion of handling multiple SignatureBlocks.


# Information Model {#sec-data-model}

This section describes the semantics of the key claims as part of the information
model.

The envelop structure is:

~~~asn.1
PkixAttestation ::= SEQUENCE {
    tbs TbsPkixAttestation,
    signatures SEQUENCE SIZE (0..MAX) of SignatureBlock
}

TbsPkixAttestation ::= SEQUENCE {
    version INTEGER,
    reportedEntities SEQUENCE SIZE (1..MAX) OF ReportedEntity
}

SignatureBlock ::= SEQUENCE {
   certChain SEQUENCE of Certificate,
   signatureAlgorithm AlgorithmIdentifier,
   signatureValue OCTET STRING
}
~~~

A PkixAttestation message is composed of a protected section known as the To-Be-Signed or TBS. The integrity of the To-Be-Signed section is ensured with one or multiple cryptographic signatures over the content of the section. There is a provision to carry the X.509 certificates supporting the signature(s).

The TBS section is composed of a version number, to ensure future extensibility, and a sequence of reported entities.

For compliance with this specification, `TbsPkixAttestation.version` MUST be `1`.
This envelope format is not extensible; future specifications which make compatibility-breaking changes MUST increment the version number.

EDNOTE: do we want extension marks on the TbsAttestation object? I can see pros and cons to doing that.

`SignatureBlock.certChain` MUST contain at least one X.509 certificate as per {{RFC5280}}.
While there might exist attesting environments which use out-of-band or non-X.509 mechanisms for communicating
the AK public key to the Verifier, these SHALL be considered non-compliant with this specification.


The attribute format is intended to be generic, flexible, and extensible with a default set of attributes defined in this document. Attributes are grouped into entities; an entity can be either a key, a platform, or a request containing a set of claims that are requested to be filled by the attesting environment.

~~~asn.1
ReportedEntity ::= SEQUENCE {
    entityType         OBJECT IDENTIFIER,
    reportedAttributes SEQUENCE SIZE (1..MAX) OF ReportedAttribute
}
~~~

A reported entity is a unit of observation measured by the Attester (the HSM). In this specification, there are three types of entities defined:
- Platform Entity : An entity that reports attributes about the platform, itself. A PKIX Attestation MAY contain only one Platform Entity.
- Key Entity : An entity that represents a single cryptographic key found in a HSM ad its associated attributes. A PKIX Attestation MAY contain one or more Key Entities.
- Transaction Entity : An entity reporting attributes observed from the request itself. A PKIX Attestation MAY contain only one Transaction Entity.

A reported entity is composed of an Object Identifier (OID), specifying the entity type, and a sequence of reported attributes associated with the entity.

Although this specification defines only three types of entities, implementations MAY define additional entity types by registering additional OIDs.

An Attester (HSM) which is requested to provide information about unrecognized entity types MUST fail the operation.

A Verifier which encounters an unrecognized entity type MAY ignore it.

~~~asn.1
id-pkix-attest                    OBJECT IDENTIFIER ::= { 1 2 3 999 }
id-pkix-attest-entity-type        OBJECT IDENTIFIER ::= { id-pkix-attest 0 }
id-pkix-attest-entity-transaction OBJECT IDENTIFIER ::= { id-pkix-attest-entity-type 0 }
id-pkix-attest-entity-platform    OBJECT IDENTIFIER ::= { id-pkix-attest-entity-type 1 }
id-pkix-attest-entity-key         OBJECT IDENTIFIER ::= { id-pkix-attest-entity-type 2 }
id-pkix-attest-entity-request     OBJECT IDENTIFIER ::= { id-pkix-attest-entity-type 3 }
~~~

TODO: do we need entity types for "platform policy" and "key policy" ?

A PKIX Attestation MUST NOT contain more than one platform entity since duplicate and conflicting platform claims across multiple platform entities can easily lead to security bugs.
A parser MUST fail with an error if it encouters multiple platform entities.

A PKIX Attestation MUST NOT contain more than one transaction entity. A transaction entity contains attributes that are related to the request such as a "nonce".
A parser MUST fail with an error if it encouters multiple transaction entities.

A PKIX Attestation MAY contain one or more application key entities. Each key entity SHOULD describe a unique application key. Multiple ReportedEntity objects of type `entity-key` that describe the same application key SHOULD be avoided since different or conflicting claims could lead to security issues on the part of the Verifier or Relying Party.

TODO: note that we need to be careful about whether it is allowed to include the AK(s) and other "platform-owned" keys in the set of keys you can attest, or only attesting application keys.




Each reported attribute is composed of an Object Identifier (OID), identifying the type of the attribute, and a value which must be one of the prescribed data types.

~~~asn.1
ReportedAttribute ::= SEQUENCE {
    attributeType      OBJECT IDENTIFIER,
    value              OPTIONAL AttributeValue
}

AttributeValue :== CHOICE {
   bytes       [0] IMPLICIT OCTET STRING
   utf8String  [1] IMPLICIT UTF8String,
   bool        [2] IMPLICIT BOOLEAN,
   time        [3] IMPLICIT GeneralizedTime,
   int         [4] IMPLICIT INTEGER,
   oid         [5] IMPLICIT OBJECT IDENTIFIER
}
~~~

An attribute type is generally associated with a single entity type. In the following sub-sections, defined attributes are grouped according to their related entity types.

There are circumstances where an attribute type can be repeated for a given entity while other attribute types are unique.
For example, the `hwmodel`, `uptime`, and `fipsboot` attributes are not allowed to have multiple instances since these are global measurements of the platform. However, other attribute types such as `usermods` allow multiple instances as an HSM can have more than one user module loaded. The tables below list for each attribute type whether multiples are allowed.
For attribute types that do not allow multiples, a parser MUST fail with an error if it encouters multiple instances.
For attribute types that allow multiples, a parser MUST treat each one as an independent attribute and MUST NOT, for example, consider later ones to overwrite the previous one. Appraisal policies and profiles SHOULD be clear about how to handle multiples when requiring attribute types that allow multiples.

PKIX Attestation Requests are discussed in {{sec-reqs}}.
In the tables in the sections that follow, the column "Request Contains a Value" specifies whether,
when the given attribute appears in a request, whether it is to be a valued or un-valued request attribute as described in {{sec-reqs}}.




## Transaction Attributes

A default and vendor-agnostic set of transaction attributes is defined in this section.

These attribute types MAY be contained within a transaction entity; i.e. an entity identified by `id-pkix-attest-entity-transaction`.

| Attribute       | AttributeValue  | Reference           | Multiple Allowed | Request Contains a Value | Description     |
| ---             | ---             | ---                 | ---              | ---           | ---             |
| nonce           | bytes           | {{&SELF}}           | No               | MUST          | Repeats a "nonce" provided during the atttestation request. |
| timestamp       | time            | {{-eat}} | No        | MUST NOT      | The time at which this attestation was generated. Corresponds to EAT IAT claim. |

### nonce

The nonce attribute is used to provide "freshness" quality as to the information provided by the Attester (HSM) in the PkixAttestation message. A client requesting a PkixAttestation message MAY provide a nonce value as part of the request. This nonce value, if provided, SHOULD be repeated as an attribute to the transaction entity.

### time

The time at which this attestation was generated, according to the internal system clock of the HSM.

Note that it is common for HSMs to not have an accurate system clock; consider an HSM for a root CA kept offline and booted up infrequently in an local network segregated from all other network, or a smart card which boots up only when held against an NFC reader.
Implementers of emitters SHOULD include this attribute only if the device reliably knows its own time (for example has had recent contact with an NTP server).
Implementers of parsers SHOULD be wary of trusting the contents of this attribute. A challenge-response protocol that makes use of the nonce attribute is a far more reliable way of establishing freshness.


## Platform Attributes

A default and vendor-agnostic set of platform attributes is defined in this section.

These attribute types MAY be contained within a platform entity; i.e. an entity identified by `id-pkix-attest-entity-platform`.

| Attribute| AttributeValue| Reference| Multiple Allowed| Request Contains a Value| Description|
| ---      | ---           | ---      | ---             | ---                     | ---        |
| vendor          | utf8String      | {{&SELF}}           | No               | MUST NOT  | A human-readable string by which the vendor identifies themself. |
| oemid           | bytes           | {{-eat}} | No               | MUST NOT  | The EAT OEM ID as defined in {{-eat}}. |
| hwmodel         | utf8String      | {{-eat}} | No               | MUST NOT  | Model or product line of the hardware module. |
| hwserial        | utf8String      | {{&SELF}}           | No               | MUST NOT  | Serial number of the hardware module, often matches the number engraved or stickered on the case. |
| swversion       | utf8String      | {{-eat}} | No               | MUST NOT  | A text string identifying the firmware or software running on the HSM. |
| dbgstat         | int             | {{-eat}} | No               | MUST NOT  | Indicates whether the HSM is currently in a debug state, or is capable in the future of being turned to a debug state. Semantics and integer codes are defined in {{-eat}}. |
| uptime          | int             | {{-eat}} | No               | MUST NOT  | Contains the number of seconds that have elapsed since the entity was last booted. |
| bootcount       | int             | {{-eat}} | No               | MUST NOT  | Contains a count of the number of times the entity has been booted. |
| usermods        | utf8String      | {{&SELF}}           | Yes              | MUST NOT  | This attribute lists user modules currently loaded onto the HSM in a human readable format, preferabbly JSON. |
| fipsboot        | bool            | {{-fips}}        | No               | MUST NOT  | Indicates whether the devices is currently running in FIPS mode. |
| fipsver         | utf8String      | {{-fips}}        | No               | MUST NOT  | Indicates the version of the FIPS CMVP standard that is being enforced. At time of writing this is typically "FIPS 140-2" or "FIPS 140-3". |
| fipslevel       | int             | {{-fips}}        | No               | MUST NOT  | Indicates the FIPS Level to which the device is currently operating in compliance with. |
| envid           | utf8String      | {{&SELF}}           | Yes              | MAY       | An environment ID, which will typically be a URI, UUID, or similar. |
| envdesc         | utf8String      | {{&SELF}}           | Yes              | MUST NOT  | Further description of the environment. |

TODO: find the actual reference for "FIPS Mode" -- FIPS 140-3 does not define it (at least not the 11 page useless version of 140-3 that I found).

Each attribute has an assigned OID, see {{sec-asn1-mod}}.

Some of the attributes defined in this specification have further details below.

### usermods

Most HSMs have some concept of trusted execution environment where user software modules can be loaded inside the HSM to run with some level of privileged access to the application keys. This attribute lists user modules currently loaded onto the HSM in a human readable format, preferably JSON.

### fipsboot, fipsver and fipslevel

FIPS 140-3 CMVP validation places stringent requirements on the mode of operation of the device and the cryptography offered by the module, including only enabling FIPS-approved algorithms, certain requirements on entropy sources, and extensive start-up self-tests. FIPS 140-3 offers compliance levels 1 through 4 with increasingly strict requirements. Many HSMs include a configuration setting that allows the device to be taken out of FIPS mode and thus enable additional functionality or performance, and some offer configuration settings to change between compliance levels.

The boolean attribute `fipsboot` indicates whether the device is currently operating in FIPS mode. For most HSMs, changing this configuration setting from `fipsboot=true` to `fips-boos=false` is destructive and will result in zeroization of all cryptographic keys held within the module.

The UTF8String attribet `fipsver` indicates the version of the FIPS CMVP specification with which the device's operational mode is compliant. At the time of writing, the strings "FIPS 140-2" or "FIPS 140-3" SHOULD be used.

The integer attribute `fipslevel` indicates the compliance level to which the device is currently operating and MUST only be 1, 2, 3, or 4. The `fipslevel` attribute has no meaning if `fipsboot` is absent or `false`.

The FIPS status information in a PKIX Attestation indicates only the mode of operation of the device and is not authoritative of its validation status.
This information is available on the NIST CMVP website or by contacting the device vendor.
As an example, some devices may have the option to enable FIPS mode in configuration even if the vendor has not sumbitted this model for validation. As another example, a device may be running in a mode consistent with FIPS Level 3 but the device was only validated and certified to Level 2.
A Relying Party wishing to know the validation status of the device MUST couple the device state information contained in the attestation with a valid FIPS CMVP certificate for the device.

### envid

An identifier for an environment to which the attested keys belong. These will be an a vendor-chosen format, but are constrained to ASCII as URIs, UUID, and similar types of identifiers are envisioned.

There MAY be multiple envid attributes if the attested keys simultaneously belong to multiple environments.

Note that by including envid as a Platform Attribute, this implies that it applies to all attested key entities. If the HSM needs to attest multiple keys across multiple disjoint environments, then multiple PKIXAttestations are required. This naturally enforces privacy constraints of only attesting a single environment at a time.

If an envdid request attribute contains a value, this means that the Presenter is requesting that only keys belogning to the given environment be included in the returned attestation.

### envdesc

Further description of the environment beyond hwvendor, hwmodel, hwserial, swversion; for example if there is a need to describe multiple logical partitions within the same device. Contents could be a human-readable description or other identifiers.


## Key Attributes

A default and vendor-agnostic set of key attributes is defined in this section.

These attribute types MAY be contained within a key entity; i.e. an entity identified by `id-pkix-attest-entity-key`.

| Attribute       | AttributeValue  | Reference           | Multiple Allowed | Request Contains a Value | Description     |
| ---             | ---             | ---                 | ---              | ---             | ---           |
| identifier      | utf8String      | {{&SELF}}           | Yes              | MAY             | Identifies the subject key, with a vendor-specific format which could be numeric, UUID, or other textual identifier. |
| spki            | bytes           | {{&SELF}}           | No               | MAY             | A complete DER-encoded SubjectPublicKeyInfo representing the public key associated with the asymetric key pair being attested. |
| purpose         | bytes           | [PKCS11]            | No               | MAY             | Defines the intended usage for the key. |
| extractable     | bool            | [PKCS11]            | No               | MAY             | Indicates if the key is able to be exported from the module. Corresponds directly to PKCS#11 CKA_EXTRACTABLE. |
| sensitive       | bool            | [PKCS11]            | No               | MAY             | Indicates that the key cannot leave the module in plaintext. Corresponds directly to PKCS#11 CKA_SENSITIVE. |
| never-extractable | bool          | [PKCS11]            | No               | MAY             | Indicates if the key was able to be exported from the module. Corresponds directly to PKCS#11  CKA_NEVER_EXTRACTABLE. |
| local           | bool            | {{&SELF}}           | No               | MAY             | Indicates whether the key was generated locally or imported. |
| expiry          | time            | {{&SELF}}           | No               | MAY             | Defines the expiry date or "not after" time for the key. |
| protection      | bytes           | {{&SELF}}           | No               | MAY             | Indicates any additional key protection properties. |

PKCS#11 private key attributes can be somewhat complex to parse, especially as their exact meanings can vary by the key type and the exact details of key export mechanisms supported by the HSM.

In most cases, the Verifier of a PKIX Attestation will want to know simply that the key is in hardware and cannot be extracted to be used with a software cryptographic module. A setting of `extractable=false` satisfies this requirement. Generally `extractable=true && sensitive=true` also satisfies this requirement as the key cannot be extracted in plaintext, but only under key wrap. This is common in HSM clustering scenarios, and is also common in scenarios where keys are exported under wrap so that they can be stored in an off-board database for re-import later, thus allowing the HSM to protect and manage a much larger set of keys than it has internal memory for. The `never-extractable` and `local` attributes give additional assurance that the key has always been in hardware and was not imported from software.

### purpose

TODO: probably need to define a mapping from PKCS#11 CKA enums to a bit-indexed byte array.

### protection

Indicates any additional key protection properties around use or modification of this key. These are generalized properties and will not apply the same way to all HSM vendors. Consult vendor documentation for the in-context meaning of these flags.

TODO: define a bit-indexed byte array

BIT MASK / Boolean Array {DualControl (0), CardControl (1), PasswordControl (2), ...}

We may need to say that the first X are reserved for use by future RFCs that update this specification, and beyond that is private use.


## Additional Entity and Attribute Types {#sec-additional-attr-types}

It is expected that HSM vendors will register additional Entity and Attribute types by assigning OIDs from their own proprietary OID arcs to hold data describing additional proprietary key properties.

An Attester (HSM) which is requested to provide information about unrecognized Entity or Attribute types MUST fail the operation.

A Verifier which encounters an unrecognized Entity or Attribute type MAY ignore it.


## Encoding

A PKIXAttestation is to be DER encoded [X.690].

If a textual representation is required, then the DER encoding MAY be subsequently encoded into Base64.

EDNOTE: I think we have to be precise about which flavour of Base64 we are referrring to.



# Signing Procedure

The `SignatureBlock.signatureValue` signs over the DER-encoded to-be-signed attestation data
`PkixAttestation.tbs` and MUST be validated with the subject public key of the leaf
X.509 certificate contained in the `SignatureBlock.certChain`.

# Verification Procedure {#sec-verif-proc}

The `SignatureBlock.signatureValue` signs over the DER-encoded to-be-signed attestation data
`PkixAttestation.tbs` and MUST be validated with the subject public key of the leaf
X.509 certificate contained in the `SignatureBlock.certChain`.

Note that a PkixAttestation MAY contain zero or more SignatureBlocks.
A PkixAttestation with zero SignatureBlocks is unsigned, MUST be treated as un-protected and un-trusted,
and any signature validation procedure MUST fail.

More than one SignatureBlocks MAY be used to convey a number of different semantics.
For example, the HSM's Attesting Service might hold multiple Attestation Keys on different cryptographic
algorithms in order to provide algorithm redundancy in the case that one algorithm becomes cryptographically broken. In this case a Verifier would be expected to validate all SignatureBlocks. Alternatively, the HSM's Attesting Service may hold multiple Attestion Keys (or multiple X.509 certificates for the same key) from multiple operational environments to which it belongs. In this case a Verifier would be expected to only validate the SignatureBlock corresponding to its own environment. Alternatively, multiple SignatureBlocks could be used to convey counter-signatures from external parties, in which case the Verifier will need to be equipped with environment-specific verification logic. Multiple of these cases, and potentially others, could be present in a single PkixAttestation object.

Note that each SignatureBlock is a fully detached signature over the tbs content with no binding between the signed content and the SignatureBlocks, or between SignatureBlocks, meaning that a third party can add a
counter-signature of the evidence after the fact, or an attacker can remove a SignatureBlock without leaving any artifact. See {#sec-detached-sigs} for further discussion.



# Attestation Requests {#sec-reqs}

EDNOTE: MikeO: this is complex, but I'm not really sure how to define a request format in any simpler way. Ideas are welcome!

This section specifies a standardized format that a Presenter can use to request a PKIX Attestation about a specific key or set of keys, a specific environment, or containing specific attributes.

Hardware Security Modules range greatly in size and complexity from personal cryptographic tokens containing a single application key such as a smartcard acting as a personal ID card, up to clusters of enterprise-grade HSMs serving an entire cloud service.


The manufacturer of a HSM device with limited capabilities may implement a response to the attestation request which includes a fixed set of reported entities, each with a fixed set of reported attributes and parses an Attestion Request object only for the purposes of extracting the nonce.

On the other hand, an enterprise grade HSM with the capability to hold a large number of private keys is expected to be capable of parsing attestation requests such that a Presenter can request attestation of specific key(s) by their identifier, or request attestation of all keys with given key attributes within a given sub-environment of the HSM. A full implementation will also create a PKIX Attestation containing exactly the set of requested attributes so that the Presenter can fine-tune the information that it wishes to disclose to the Recipient.

A PKIX Attestation Request consists of a un-signed TbsPkixAttestation object containing a single `ReportedEntity` identified with `id-pkix-attest-entity-request`, called a request entity. A TbsPkixAttestation containing a request entity MUST NOT contain any other type of entities. Request entities MAY contain Attributes of any type; transaction, platform, key, or any additional attribute type. Any attribute contained in a request entity is called a request attribute. Request entities MUST NOT appear in PKIX Attestation response objects. The TbsPkixAttestation object of an attestation request MAY appear inside a signed PKIXAttestation for the purposes of authenticating and authorizing the requester, but the semantics of doing so are left to the implementer.

An Attester that supports Attestation Requests MUST, at the minimum, support extracting the value from a `nonce` attribute and echoing it into a `nonce` attribute within a TransactionEntity.

Some request attributes contain a value that the HSM uses as a filter or search parameter in constructing the PKIX Attestation; these are called valued requests attributes.
Other requests attributes omit the optional `value` field so that they consist of only the attribute type OID and indicate that the HSM SHOULD collect and return the appropriate measurement; these are called un-valued request attributes.
An Attester SHOULD return a PKIX Attestation containing exactly the set of attributes listed in the request, including both valued and un-valued request attributes but MAY omit requested attributes if it cannot be measured in the current device configuration.
Note that an Attestation Request will contain all request attributes inside a single request entity, but the HSM MUST sort the attributes in the response PKIX Attestation into the appropriate entity types.
For example, if the request contains the key `purpose` attribute (either valued or un-valued), then all returned key entities will contain the `purpose` attribute when this data is available for the given key.
The tables in the following sections indicate whether an attribute of the given type MUST, MAY, or MUST NOT contain a value when included in a request entity.

Generally errors should be handled gracefully by simply omitting an unfulfillable request attribute from the response.
An example would be if the `hwserial` attribute was requested but the devices does not have a serial number.
However in some cases a fatal error MAY be returned, for example if attestation of a specific key is requested by key identifier or SubjectPublicKeyInfo but the HSM does not contain a matching key.
HSMs SHOULD ignore request attributes with unrecognized type OIDs.

Generally, the Attester SHOULD NOT include additional attributes beyond those that were requested. This is to allow the Presenter to fine-tune the information that will be disclosed to the Recipient.
Further privacy concerns are discussed in {{sec-cons-privacy}}.
However, in some contexts this MAY be appropriate, for example, a request containing only a key `identifier` attribute could be responded to with the full set of platform and key attributes that apply to that key.
Discretion is left to implementers.

For both error handling and privacy reasons, the Presenter SHOULD check that the returned PKIX Attestation contains the expected attributes prior to forwarding it to the Recipient.





# Appraisal Policies and Profiles {#sec-profiles}

This section provides some sample profiles of appraisal policies that verifiers
MAY apply when evaluating evidence. These appraisal profiles represent environment-specific requirements
on the contents of the evidence and / or endorsement certificate chain.


## Key Import into an HSM

An HSM which is compliant with this draft SHOULD validate any PKIX Key Attestations that are provided
along with the key being imported.

The SignatureBlocks MUST be validated and MUST chain to a trust anchor known to the HSM. In most cases this will
be the same trust anchor that endorsed the HSMs own AK, but the HSM MAY be configured with set of third party trust anchors from which it will accept key attestations.

If the HSM is operating in FIPS Mode, then it MUST only import keys from HSMs also operating in FIPS Mode.

The claims `key-purpose`, `key-extractable`, `key-never-extractable`, `key-local` MUST be checked and honoured during key import, which typically means that after import, the key MUST NOT claim a stronger protection property than it had on the previous hardware. In other words, Key Attestation allows and requires that key protection properties be preserved over export / import operations between different HSMs, and this format provides a vendor-agnostic
way to acheive this.

How to handle errors is outside the scope of this specification and is left to implementors; for example the
key import MAY be aborted, or a prompt MAY be given to the user administrator, or any similar reasonable error handling logic.




## CA/Browser Forum Code-Signing

TODO: ... intro text

The subscriber MUST:

* Provide the CA with a CSR containing the subscriber key.
* Provide an attestation token as per this specification describing the private key protection properties of the subscriber's private key. This token MAY be transported inside the CSR as per draft-ietf-lamps-csr-attest, or it MAY be transported adjacent to the CSR over any other certificate enrollment mechanism.

The CA / RA / RP / Verifier MUST:

* Ensure that the subscriber key which is the subject of the CSR is also described by a KAT by matching either the key fingerprint or full SubjectPublicKeyInfo.
* The hardware root-of-trust described by a PAT has a valid and active FIPS certificate according to the NIST CMVP database.
* The attestation signing key (AK) which has signed the attestation token chains to a root certificate that A) belongs to the hardware vendor described in the PAT token, and B) is trusted by the CA / RA / RP / Verifier to endorse hardware from this vendor, for example through a CA's partner program or through a network operator's device on-boarding process.
* The key is protected by a module running in FIPS mode. The parsing logic is to start at the leaf KAT token that matches the key in the CSR and parsing towards the root PAT ensuring that there is at least one `fipsboot=true` and no `fipsboot=false` on that path.



# ASN.1 Module {#sec-asn1-mod}

~~~ asn.1

<CODE STARTS>

{::include Pkix-Key-Attest-2025.asn}

<CODE ENDS>

~~~

# IANA Considerations

Please replace "{{&SELF}}" with the RFC number assigned to this document.

TODO: list out all the OIDs that need IANA registration.



# Security Considerations

A Verifier MAY reject a PKIX Attestation if it lacks required attributes per their
appraisal policy. For example, if a Relying Party mandates a FIPS-certified device,
it SHOULD reject evidence lacking sufficient information to verify the device's FIPS
certification status.


## Simple to Implement {#sec-cons-simple}

The nature of attestation requires the attestation service to be implemented in an extremely privileged position within the HSM so that it can collect measurements of both the hardware environment and the application keys being attested. For many HSM and TPM architectures, this will place the Attestation Service inside the "HSM kernel" and potentially subject to FIPS 140-3 or Common Criteria validation and change control. For both security and compliance reasons there is incentive for the emitting and parsing logic to be simple and easy to implement correctly. Additionally, when the data formats contained in this specification are parsed within an HSM boundary -- that would be parsing a request entity, or parsing an attestation produced by a different HSM -- implementers SHOULD opt for simple logic that rejects any data that does not match the expected format instead of attempting to be flexible.

In particular, Attesting Services SHOULD generate the attestation object from scratch and avoid copying any content from the request. Attesting Services MUST NOT allow unrecognized attributes or any attribute value other than the nonce to be echoed from the request into the attestation object.

## Detached Signatures {#sec-detached-sigs}

TODO beef this up

No indication within the tbs content about what or how many signatures to expect.

A SignatureBlock can be trivially stripped off without leaving any evidence.

When multiple SignatureBlocks are used for providing third party counter-signatures, note that the counter signature only covers the tbs content and not existing SignatureBlocks.

## Privacy {#sec-cons-privacy}

Often, a TPM will host cryptographic keys for both the kernel and userspace of a local operating system but a Presenter may only represents a single user or application.
Similarly, a single enterprise-grade Hardware Security Module will often host cryptographic keys for an entire multi-tenant cloud service and the Presenter or Reciever or Recipient belongs only to a single tenant. For example the HSM backing a TLS-terminating loadbalancer fronting thousands of un-related web domains.
In these cases, disclosing that two different keys reside on the same hardware, or in some cases even disclosing the existance of a given key, let alone its attributes, to an unauthorized party would constitute an egregious privacy violation.

Implementions SHOULD be careful to avoid over-disclosure of information, for example by authenticating the Presenter as described in {{sec-cons-auth-the-presenter}} and only returning results for keys and envirnments for which it is authorized.
In absence of an existing mechanism for authenticating and authorizing administrative connections to the HSM, the attestation request MAY be authenticated by embedding the TbsPkixAttestation of the request inside a PKIXAttestation signed with a certificate belogning to the Presenter.

Furthermore, enterprise and cloud-services grade HSMs SHOULD support the full set of attestation request functionality described in {{sec-reqs}} so that Presenters can fine-tune the content of a PKIX Attestation such that it is appropriate for the intended Recipient.


## Authenticating and Authorizing the Presenter {#sec-cons-auth-the-presenter}

The Presenter represents a priviledged role within the architecture of this specification as it gets to learn about the existence of application keys and their protection properties, as well as details of the platform.
The Presenter is in the position of deciding how much information to disclose to the Recipient, and to request a suitably redacted attestation from the HSM.

For personal cryptographic tokens it might be appropriate for the attestation request interface to be un-authenticated. However, for enterprise and cloud-services grade HSMs the Presenter SHOULD be authenticated using the HSM's native authentication mechanism. The details will be HSM-specific and are thus left up to the implementer, however it is RECOMMENDED to implement an authorization framework similar to the following.

A Presenter SHOULD be allowed to request attestation for any application keys which it is allowed to use.
For example, a TLS application that is correctly authenticated to the HSM in order to use its TLS keys SHOULD be able to request attestation of those same keys without needing to perform any additional authentication or requiring any additional roles or permissions.
HSMs that wish to allow a Presenter to request attestation of keys which is not allowed to use, for example for the purposes of displaying HSM status information on an administrative console or UI, SHOULD have a "Attestation Requester" role or permission and SHOULD enforce the HSM's native access controls such that the Presenter can only retrieve attestations for keys for which it has read access.


## Proof-of-Possession of Application Keys

With asymmetric keys within a Public Key Infrastructure (PKI) it is common to require a key holder to prove that they are in control of the private key by using it. This is called "proof-of-possession (PoP)". This specification intentionally does not provide a mechnaism for PoP of application keys and relies on the Presenter, Recipient, Verifier, and Relying Party trusting the Attester to correctly report the cryptographic keys that it is holding.

It would be easy to add a PoP Key Attribute that uses the attested application key to sign over, for example, the Transaction Entity, however this is a bad idea and MUST NOT be added as a custom attribute for several reasons.

First, an application key intended, for example, for TLS SHOULD only be used with the TLS protocol and introducing a signature oracle whereby the TLS application key is used to sign attestation content could lead to cross-protocol attacks whereby the attacker submits a nonce value which is in fact not random but is crafted in such a way as to appear as a valid message in some other protocol context or exploit some other weakness in the signature algorithm.

Second, the Presenter who has connected to the HSM to request an attestation may have permissions to view the requested application keys but not permission to use them, as in the case where the Presenter is an administrative UI displaying HSM status information to an systems administrator or auditor.
Requiring the Attestation Service to use the attested application keys could, in some architectures, require the Attestation Service to resolve complex access control logic and handle complex error conditions for each requested key, which violates the "simple to implement" design principle outlined in {{sec-cons-simple}}. More discussion of authenticating the Presenter can be found in {{sec-cons-auth-the-presenter}}.


In cases where explicit PoP is required for a given attested application key, it MUST be done as part of the regular usage protocol for which that key is intended and performed through the HSM's regular application interface, not its attestation interface. For example, PoP could be performed by signing a Certificate Signing Request (CSR), through a PKI enrollment protocol such as Certificate Management Protocol (CMP) which includes a challenge-response PoP, by using the key within a TLS handshake, or some other protocol which is part of the key's intended usage.




--- back

# Samples

A reference implementation of this specification can be found at https://github.com/hannestschofenig/keyattestation

It produces the following sample attestation:

~~~
{::include sampledata/idea3/sample1.txt}
~~~

# Acknowledgements

This specification is the work of a design team created by the chairs
of the RATS working group. This specification has been developed
based on discussions in that design team and also with great amounts of
input taken from discussions on the RATS mailing list.

