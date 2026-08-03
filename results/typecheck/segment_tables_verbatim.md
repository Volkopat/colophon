source file: C:\Users\dekay\dicom-validator\2026c\docbook\part03.xml bytes 25448510

tables in part03: 1133
==============================================================================
TABLE C.8.20-4
==============================================================================
xml:id: table_C.8.20-4
caption: Segment Description Macro Attributes
------------------------------------------------------------------------------
ROW 00 | Attribute Name | Tag | Type | Attribute Description
ROW 01 | Segment Number | (0062,0004) | 1 | Identification number of the Segment. The Value of Segment Number (0062,0004) shall be unique within the Segmentation Instance in which it is created. See .
ROW 02 | Segment Label | (0062,0005) | 1 | User-defined label identifying this Segment. This may be the same as Code Meaning (0008,0104) of Segmented Property Type Code Sequence (0062,000F).
ROW 03 | Segment Description | (0062,0006) | 3 | User-defined description for this Segment.
ROW 04 | Segment Algorithm Type | (0062,0008) | 1 | Type of algorithm used to generate the Segment. Enumerated Values: AUTOMATIC calculated Segment SEMIAUTOMATIC calculated Segment with user assistance MANUAL user-entered Segment
ROW 05 | Include | May not be necessary if the anatomy is implicit in the Segmented Property Type Code Sequence. More than one Item in Anatomic Region Sequence (0008,2218) may be used when a region of interest spans multiple anatomical locations and there is not a single pre-coordinated code describing the combination of locations. There is no requirement that the multiple locations be contiguous.
ROW 06 | Segmented Property Category Code Sequence | (0062,0003) | 1 | Sequence defining the general category of the property the Segment represents. Only a single Item shall be included in this Sequence.
ROW 07 | >Include | B .
ROW 08 | Segmented Property Type Code Sequence | (0062,000F) | 1 | Sequence defining the specific property the Segment represents. "Property" is used in the sense of meaning "what the segmented voxels represent", whether it be a physical or biological object, be real or conceptual, having spatial, temporal or functional extent or not. I.e., it is what the Segment "is" (as opposed to some feature, attribute, quality, or characteristic of it, like color or shape or size). Only a single Item shall be included in this Sequence.
ROW 09 | >Include | B .
ROW 10 | >Segmented Property Type Modifier Code Sequence | (0062,0011) | 3 | Sequence defining the modifier of the property type of this Segment. One or more Items are permitted in this Sequence.
ROW 11 | >>Include | D . For Retinal Segmentation Surfaces, laterality is not typically specified.
ROW 12 | Tracking ID | (0062,0020) | 1C | A text label used for tracking a finding or feature, potentially across multiple reporting objects, over time. This label shall be unique within the domain in which it is used. Required if Tracking UID (0062,0021) is present. May or may not have the same Value as Segment Label (0062,0005). Related SR Instances may exist, for example, to record measurements related to this Segment, but need not exist for this Attribute to be used. This Attribute will have the same Value as the value of the (112039, DCM, "Tracking Identifier") Content Item in SR Instances that reference this Segment in this Segmentation Instance.
ROW 13 | Tracking UID | (0062,0021) | 1C | A unique identifier used for tracking a finding or feature, potentially across multiple reporting objects, over time. Required if Tracking ID (0062,0020) is present. Related SR Instances may exist, for example, to record measurements related to this Segment, but need not exist for this Attribute to be used. This Attribute will have the same Value as the value of the (112040, DCM, "Tracking Unique Identifier") Content Item in SR Instances that reference this Segment in this Segmentation Instance.
ROW 14 | Definition Source Sequence | (0008,1156) | 3 | Instances containing the source of the Segment information. Only a single Item is permitted in this Sequence.
ROW 15 | >Include .
ROW 16 | >Referenced ROI Number | (3006,0084) | 1C | The Value of ROI Number (3006,0022) in the referenced SOP Instance that identifies the ROI that is the origin of the Segment information. Required if Referenced SOP Class UID (0008,1150) is "1.2.840.10008.5.1.4.1.1.481.3" (RT Structure Set Storage).
ROW 17 | Include

==============================================================================
TABLE C.8.20-2
==============================================================================
xml:id: table_C.8.20-2
caption: Segmentation Image Module Attributes
------------------------------------------------------------------------------
ROW 00 | Attribute Name | Tag | Type | Attribute Description
ROW 01 | Image Type | (0008,0008) | 1 | Image identification characteristics. Value 1 shall be DERIVED. Value 2 shall be PRIMARY. No other values shall be present.
ROW 02 | Include
ROW 03 | Samples per Pixel | (0028,0002) | 1 | Number of samples (planes) in this image. Enumerated Values: 1
ROW 04 | Photometric Interpretation | (0028,0004) | 1 | Specifies the intended interpretation of the pixel data. Enumerated Values if Segmentation Type (0062,0001) is BINARY or FRACTIONAL: MONOCHROME2 Enumerated Values if Segmentation Type (0062,0001) is LABELMAP: MONOCHROME2 PALETTE COLOR
ROW 05 | Pixel Representation | (0028,0103) | 1 | Data representation of pixel samples. Enumerated Values: 0
ROW 06 | Bits Allocated | (0028,0100) | 1 | Number of bits allocated for each pixel sample. See . Enumerated Values if Segmentation Type (0062,0001) is BINARY: 1 Enumerated Values if Segmentation Type (0062,0001) is FRACTIONAL: 8 Enumerated Values if Segmentation Type (0062,0001) is LABELMAP: 8 16
ROW 07 | Bits Stored | (0028,0101) | 1 | Number of bits stored for each pixel sample. See . Enumerated Values if Segmentation Type (0062,0001) is BINARY: 1 Enumerated Values if Segmentation Type (0062,0001) is FRACTIONAL: 8 Enumerated Values if Segmentation Type (0062,0001) is LABELMAP and Bits Allocated (0028,0100) is 8: 8 Enumerated Values if Segmentation Type (0062,0001) is LABELMAP and Bits Allocated (0028,0100) is 16: 16
ROW 08 | High Bit | (0028,0102) | 1 | Most significant bit for pixel sample data. See . Enumerated Values if Segmentation Type (0062,0001) is BINARY: 0 Enumerated Values if Segmentation Type (0062,0001) is FRACTIONAL: 7 Enumerated Values if Segmentation Type (0062,0001) is LABELMAP and Bits Allocated (0028,0100) is 8: 7 Enumerated Values if Segmentation Type (0062,0001) is LABELMAP and Bits Allocated (0028,0100) is 16: 15
ROW 09 | Lossy Image Compression | (0028,2110) | 1 | Specifies whether an Image has undergone lossy compression (at a point in its lifetime), or is derived from lossy compressed images. Enumerated Values: 00 Image has not been subjected to lossy compression. 01 Image has been subjected to lossy compression. Once this Attribute has been set to a Value of "01" it shall not be reset. See and .
ROW 10 | Lossy Image Compression Ratio | (0028,2112) | 1C | Describes the approximate lossy compression ratio(s) that have been applied to this image. See . Required if present in the source images or this IOD Instance has been compressed.
ROW 11 | Lossy Image Compression Method | (0028,2114) | 1C | A label for the lossy compression method(s) that have been applied to this image. See . Required if present in the source images or this IOD Instance has been compressed. See .
ROW 12 | Segmentation Type | (0062,0001) | 1 | The type of encoding used to indicate the presence of the segmented property at a pixel/voxel location. Enumerated Values: BINARY FRACTIONAL LABELMAP See .
ROW 13 | Segmentation Fractional Type | (0062,0010) | 1C | For fractional segmentation encoding, the meaning of the fractional value. Required if Segmentation Type (0062,0001) is FRACTIONAL. See for Enumerated Values.
ROW 14 | Maximum Fractional Value | (0062,000E) | 1C | Specifies the value that represents a probability of 1 or complete occupancy. There shall be no values in Pixel Data (7FE0,0010) greater than this value. Required if Segmentation Type (0062,0001) is FRACTIONAL.
ROW 15 | Segments Overlap | (0062,0013) | 3 | Whether or not any Segments in this Instance overlap. I.e., whether or not any pixel is or might be in more than one Segment. Enumerated Values: YES Some Segments overlap UNDEFINED Some Segments might overlap NO No Segments overlap See . If present, shall be NO if Segmentation Type (0062,0001) is LABELMAP. If the value is NO, then a receiving application to which this matters can be assured that no Segments overlap and does not need to check every pixel. If the value is UNDEFINED or YES, or the Attribute is absent, then a receiving application might need to check every pixel in every Segment.
ROW 16 | Segment Sequence | (0062,0002) | 1 | Describes the Segments that are contained within the data. One or more Items shall be included in this Sequence. The Items of this Sequence are not required to be in any particular order, i.e., are not required to be ordered by Segment Number (0062,0004).
ROW 17 | >Include
ROW 18 | >Segment Algorithm Name | (0062,0009) | 1C | The name(s) of algorithm(s) used to generate the Segment. Required if Segment Algorithm Type (0062,0008) is not MANUAL.
ROW 19 | >Segmentation Algorithm Identification Sequence | (0062,0007) | 3 | A description of how this Segment was derived. Algorithm Name (0066,0036) within this Sequence may be identical to Segment Algorithm Name (0062,0009). One or more Items are permitted in this Sequence. Previously, the Segment Surface Generation Algorithm Identification Code Sequence (0066,002D) was used, but it has been replaced in this Module, since not all segmentation algorithms involve surface generation. See PS3.3-2016d .
ROW 20 | >>Include | B .
ROW 21 | >Recommended Display Grayscale Value | (0062,000C) | 3 | A default single gray unsigned value in which it is recommended that the maximum pixel value in this Segment be rendered on a monochrome display. The units are specified in P-Values from a minimum of 0000H (black) up to a maximum of FFFFH (white). The maximum P-Value for this Attribute may be different from the maximum P-Value from the output of the Presentation LUT, which may be less than 16 bits in depth.
ROW 22 | >Recommended Display CIELab Value | (0062,000D) | 3 | A default color value in which it is recommended that Segment be rendered on a color display. The units are specified in PCS-Values, and the value is encoded as CIELab. See . Shall not be present if Segmentation Type (0062,0001) is LABELMAP and Photometric Interpretation (0028,0004) is PALETTE COLOR.

==============================================================================
WHICH TABLES CONTAIN THE THREE TAGS
==============================================================================

--- (0062,0008) ---
  table_C.8.20-2             | Segmentation Image Module Attributes
      ROW: >Segment Algorithm Name | (0062,0009) | 1C | The name(s) of algorithm(s) used to generate the Segment. Required if Segment Algorithm Type (0062,0008) is not MANUAL.
  table_C.8.20-4             | Segment Description Macro Attributes
      ROW: Segment Algorithm Type | (0062,0008) | 1 | Type of algorithm used to generate the Segment. Enumerated Values: AUTOMATIC calculated Segment SEMIAUTOMATIC calculated Segment with user assistance MANUAL user-entered Segment
  table_C.8.20-5             | Height Map Segmentation Image Module Attributes
      ROW: >Segment Algorithm Name | (0062,0009) | 1C | Name of algorithm used to generate the segment. Required if Segment Algorithm Type (0062,0008) is not MANUAL.
  table_C.8.20-5             | Height Map Segmentation Image Module Attributes
      ROW: >Segmentation Algorithm Identification Sequence | (0062,0007) | 1C | A description of how this segment was derived. Algorithm Name (0066,0036) within this Sequence may be identical to Segment Algorithm Name (0062,0009). Required if Segment Algorithm Type (0062,0008) is not MANUAL. Only a single Item shall be included in this Sequence.

--- (0062,0009) ---
  table_C.8.20-2             | Segmentation Image Module Attributes
      ROW: >Segment Algorithm Name | (0062,0009) | 1C | The name(s) of algorithm(s) used to generate the Segment. Required if Segment Algorithm Type (0062,0008) is not MANUAL.
  table_C.8.20-2             | Segmentation Image Module Attributes
      ROW: >Segmentation Algorithm Identification Sequence | (0062,0007) | 3 | A description of how this Segment was derived. Algorithm Name (0066,0036) within this Sequence may be identical to Segment Algorithm Name (0062,0009). One or more Items are permitted in this Sequence. Previously, the Segment Surface Generation Algorithm Identification Code Sequence (0066,002D) was used, but it has been replaced in this Module, since not all segmentation algorithms involve surface generation. See PS3.3-2016d .
  table_C.8.20-5             | Height Map Segmentation Image Module Attributes
      ROW: >Segment Algorithm Name | (0062,0009) | 1C | Name of algorithm used to generate the segment. Required if Segment Algorithm Type (0062,0008) is not MANUAL.
  table_C.8.20-5             | Height Map Segmentation Image Module Attributes
      ROW: >Segmentation Algorithm Identification Sequence | (0062,0007) | 1C | A description of how this segment was derived. Algorithm Name (0066,0036) within this Sequence may be identical to Segment Algorithm Name (0062,0009). Required if Segment Algorithm Type (0062,0008) is not MANUAL. Only a single Item shall be included in this Sequence.

--- (0062,0007) ---
  table_C.8.20-2             | Segmentation Image Module Attributes
      ROW: >Segmentation Algorithm Identification Sequence | (0062,0007) | 3 | A description of how this Segment was derived. Algorithm Name (0066,0036) within this Sequence may be identical to Segment Algorithm Name (0062,0009). One or more Items are permitted in this Sequence. Previously, the Segment Surface Generation Algorithm Identification Code Sequence (0066,002D) was used, but it has been replaced in this Module, since not all segmentation algorithms involve surface generation. See PS3.3-2016d .
  table_C.8.20-5             | Height Map Segmentation Image Module Attributes
      ROW: >Segmentation Algorithm Identification Sequence | (0062,0007) | 1C | A description of how this segment was derived. Algorithm Name (0066,0036) within this Sequence may be identical to Segment Algorithm Name (0062,0009). Required if Segment Algorithm Type (0062,0008) is not MANUAL. Only a single Item shall be included in this Sequence.
