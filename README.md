# wsi2dcm
A tool to convert the different type of wsi to dicom file.

support formats (already test .iSyntax, .mrxs, .tif, .tiff):
- iSyntax
- OpenSlide
    - Aperio (.svs, .tif, .tiff)
    - Hamamatsu (.vms, .vmu, .ndpi)
    - Leica (.scn)
    - MIRAX (.mrxs)
    - Philips (.tiff)
    - Sakura (.svslide)
    - Trestle (.tif)
    - Ventana (.bif, .tif)
    - Zeiss (.czi)
    - Generic tiled TIFF (.tif)

### You can use the following command to start the program
python wsi2dcm.py -s "source_path" -o "output_path" -m "metadata_path" -mode metadata -api Openslide

Convert WSI to DICOM WSI
"-s", "--source" 'Source path of the input files'
"-o", "--output" 'Output path for the converted files'
"-m", "--metadata", 'Path to metadata files if required'
"-mode", "--convert_mode", choices=['single_file', 'folder', 'metadata'],  help='Conversion mode'
"-api", "--convert_api", choices=['iSyntax', 'Openslide'], 'Conversion API'
