/*
 * Generated by asn1c-0.9.27 (http://lionet.info/asn1c)
 * From ASN.1 module "KeytabModule"
 * 	found in "ipa.asn1"
 * 	`asn1c -fskeletons-copy`
 */

#ifndef	_GKCurrentKeys_H_
#define	_GKCurrentKeys_H_


#include <asn_application.h>

/* Including external dependencies */
#include <OCTET_STRING.h>
#include <constr_SEQUENCE.h>

#ifdef __cplusplus
extern "C" {
#endif

/* GKCurrentKeys */
typedef struct GKCurrentKeys {
	OCTET_STRING_t	 serviceIdentity;
	
	/* Context for parsing across buffer boundaries */
	asn_struct_ctx_t _asn_ctx;
} GKCurrentKeys_t;

/* Implementation */
extern asn_TYPE_descriptor_t asn_DEF_GKCurrentKeys;

#ifdef __cplusplus
}
#endif

#endif	/* _GKCurrentKeys_H_ */
#include <asn_internal.h>
