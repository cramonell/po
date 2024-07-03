PO stands for [Process Ontology](https://cramonell.github.io/ifc/po/actual/index-en.html). It is an ontology inspired by  the entities of the [Industry Foundation Classes](https://ifc43-docs.standards.buildingsmart.org/) schema(IFC) that represent built elements and spatial configurations in the built environment. In this repository you will find two converters: a schema converter from IFC (express) to PO (owl) and a IFC-to-RDF file converter . 

## How to Use
1. **Installation**:
   - Install python in your machine
   - clone this repository
   - Install requirements : [ifcopenshell](https://ifcopenshell.org/), [rdflib](https://rdflib.readthedocs.io/en/stable/index.html)

2. **Usage**:
   - For both converters jus  run the script  either from the command line or from your prefered code editor. Each converter use a config.json file (explained below).
   - The ontology-config.json file contains the mapping between the IFC entities and the BEO entities and it is the base for both converters.

3. **Configuration PO generator ([po-gen](https://github.com/cramonell/po/tree/main/po-gen))**:
   - *output-path*: path were the output file will be saved
   - *output-format*: file format (ttl, nt, rdf/xml ...)

4. **Configuration IFC to RDF converter ([IFC-converter](https://github.com/cramonell/po/tree/main/IFC-converter))**:
   - *ifc-file-path*
   - *rdf-ouput*
        - *output-path*: path were the output file will be saved
        - *output-name*: name that will be used for the output graph file, the output geometry file, and will be appended to the base url
        - *ouput-format*: file format (ttl, nt, rdf/xml ...)
        - *base-url*: base url for the graph instances

5. **License**:
   - This project is licensed under the GNU General Public License (GNU GPL). You can find the full text of the license in the LICENSE.txt file.



