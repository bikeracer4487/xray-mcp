# AttachmentDataInput

**Category:** Input Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/attachmentdatainput.doc.html

*menu* Types INPUT_OBJECT
 # AttachmentDataInput
 Attachment Data Input

## linkGraphQL Schema definition
 `1input AttachmentDataInput {92#    A valid AttachmentDataInput must have the properties filename, mimeType and data defined.3#   In alternative, the attachmentId property can be used alone.4#   If both attachmentId and other properties are defined, attachmentId takes precedence and will be used as if it was defined alone.5# 6# 7#   Filename of the attachment.8filename: String1210#   Content Type of the attachment.11mimeType: String1513#   Data of the attachment. Base64 format.14data: String1816#   Id of an attachment.17attachmentId: String19}`
## linkRequired by
 - addEvidenceToTestRunnulladdEvidenceToTestRunStepnullMutationnullTestRunEvidenceOperationsInputTest Run Evidence Operations Input