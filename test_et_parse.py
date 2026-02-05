import xml.etree.ElementTree as ET

gml_file = "/home/kenta/programming_projects/plateau_data/udx/bldg/53393596_bldg_6697_op.gml"

NS = {
    'core': 'http://www.opengis.net/citygml/2.0',
    'bldg': 'http://www.opengis.net/citygml/building/2.0',
    'gml': 'http://www.opengis.net/gml',
}

tree = ET.parse(gml_file)
root = tree.getroot()

# Find first building
bldg = root.find('.//bldg:Building', NS)
if bldg:
    print(f"Found building: {bldg.get('{' + NS['gml'] + '}id', 'no-id')[:50]}")

    # Find LOD1Solid
    lod1 = bldg.find('.//bldg:lod1Solid', NS)
    if lod1:
        print(f"Found lod1Solid")

        # Find gml:Solid
        solid = lod1.find('gml:Solid', NS)
        if solid:
            print(f"Found gml:Solid")

            # Test findall for Polygons from solid
            polygons_from_solid = solid.findall('.//gml:Polygon', NS)
            print(f"Using solid.findall('.//gml:Polygon', NS): found {len(polygons_from_solid)} Polygons")

            # Find surfaceMembers
            surface_members = solid.findall('.//gml:surfaceMember', NS)
            print(f"Found {len(surface_members)} surfaceMembers")

            if surface_members:
                sm = surface_members[0]
                print(f"\nFirst surfaceMember tag: {sm.tag}")
                print(f"First surfaceMember attribs: {sm.attrib}")
                print(f"First surfaceMember text: {sm.text}")
                print(f"First surfaceMember has {len(list(sm))} direct children")

                # Try to find child elements
                for child in sm:
                    print(f"  Child: {child.tag}")

                # Try different approaches
                poly_ns = sm.find('gml:Polygon', NS)
                print(f"Using .find('gml:Polygon', NS): {poly_ns}")

                poly_direct = sm.find('Polygon')
                print(f"Using .find('Polygon'): {poly_direct}")

                poly_iter = [e for e in sm.iter() if 'Polygon' in e.tag]
                print(f"Using .iter() and filtering: found {len(poly_iter)} Polygons")

                if poly_iter:
                    print(f"  Polygon tag: {poly_iter[0].tag}")
