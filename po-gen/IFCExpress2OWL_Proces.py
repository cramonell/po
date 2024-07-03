from ifcopenshell import ifcopenshell_wrapper
import json
from rdflib import Graph, Namespace, Literal, URIRef, BNode 

schema_name = "IFC4X3_Add2"

# load the express IFC schema
schema = ifcopenshell_wrapper.schema_by_name(schema_name)

# Create a new graph
g = Graph()

#ontology ref specification
base_ref = "https://w3id.org/po-ifc"
if schema_name == "IFC4X3": ref_name = "IFC4_3_Processes"
elif schema_name == "IFC4X3_Add2":  ref_name = "IFC4_3/ADD2_Processes"
elif schema_name == "IFC4": ref_name = "IFC4/ADD2_TC1/OWL_Processes"
elif schema_name == "IFC2X3": ref_name = "IFC2_3/OWL_Processes"
ref = URIRef(base_ref + "#")

# Create a namespaces for the ontology
IFC = Namespace(ref)
EXPRESS = Namespace('https://w3id.org/express#')
CC = Namespace('http://creativecommons.org/ns#')
LIST = Namespace("https://w3id.org/list#")
DCE = Namespace("http://purl.org/dc/elements/1.1/")
VANN = Namespace("http://purl.org/vocab/vann/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
DOT = Namespace("https://w3id.org/dot#")

# Bind your custom prefix
g.bind("ifc", IFC)
g.bind('rdf', RDF)
g.bind('rdfs', RDFS)
g.bind('owl', OWL)
g.bind('vann', VANN)
g.bind('xsd', XSD)
g.bind('express',EXPRESS)
g.bind('cc', CC)
g.bind('list', LIST)
g.bind('dce', DCE)
g.bind('dot', DOT)

def is_supertype(entity, supertype:str):
    inheritance=[]

    while entity.supertype():
        inheritance.append(entity.supertype().name())
        entity=entity.supertype()

    for i in range(len(inheritance)):
        inheritance[i]=inheritance[i]
    
    if supertype in inheritance:
        return True
    else: return False

def get_suertypes(entity):
    inheritance=[]

    while entity.supertype():
        inheritance.append(entity.supertype().name())
        entity=entity.supertype()

    for i in range(len(inheritance)):
        inheritance[i]=inheritance[i]
    
    return inheritance

def untangle_named_type_declaration(attr_declared_type):
    last_declared_type = attr_declared_type.declared_type()
    if last_declared_type.declared_type().declared_type().as_named_type():
        untangle_named_type_declaration(last_declared_type.declared_type())
    else:
        return last_declared_type.declared_type().declared_type()

def unnest_select(select, items: list):
    for item in select.select_list():
        if not item.as_select_type():
            items.append(item)
        else: unnest_select(item, items)
    return items

def iterate_subtypes_inverse_attrs(entity, inverse_attributes):
    sup_inv_attrs =  [sup_inv_attr.name() for sup_inv_attr in entity.all_inverse_attributes()]
    for subtype in entity.subtypes():
        inverse_attributes[subtype.name()]=[inv_attr.name() for inv_attr in subtype.all_inverse_attributes() if inv_attr.name() not in sup_inv_attrs]
        if subtype.name()== 'IfcProcess': 
            inverse_attributes[subtype.name()]=[inv_attr.name() for inv_attr in subtype.all_inverse_attributes()]
        iterate_subtypes_inverse_attrs(subtype,inverse_attributes)

def add_simple_type_attr(entity_name, attr_name, type_of_attr, optional):
    #create blank nodes to add restrictions
    bnode_value = BNode()
    bnode_cardinality = BNode()

    #add range to the attribute class
    range_name = type_of_attr.declared_type().upper()
    g.add((IFC[attr_name], RDFS.range,  EXPRESS[range_name]))

    #define as functional property
    g.add((IFC[attr_name], RDF.type,  OWL.FunctionalProperty))

    #add black value and cardinality restrictions to the entity class
    g.add((IFC[entity_name], RDFS.subClassOf, bnode_value))
    g.add((IFC[entity_name], RDFS.subClassOf, bnode_cardinality))

    #Specify value restriction
    g.add((bnode_value, RDF.type, OWL.Restriction))
    g.add((bnode_value, OWL.onProperty, IFC[attr_name]))
    g.add((bnode_value, OWL.allValuesFrom, EXPRESS[range_name]))

    #Specify cardinality restriction
    g.add((bnode_cardinality, RDF.type, OWL.Restriction))
    g.add((bnode_cardinality, OWL.onProperty, IFC[attr_name]))
    if optional:g.add((bnode_cardinality, OWL.maxQualifiedCardinality,  Literal(1, datatype=XSD.nonNegativeInteger)))
    else:g.add((bnode_cardinality, OWL.qualifiedCardinality,  Literal(1, datatype=XSD.nonNegativeInteger)))
    g.add((bnode_cardinality, OWL.onClass, EXPRESS[range_name]))

def add_named_type_attr(entity_name, attr_name, type_of_attr, optional):

    if type_of_attr.declared_type().as_entity() and type_of_attr.declared_type().name() in ignore_entities:
        return  False
    
    elif type_of_attr.declared_type().as_entity():
        #as object property
        g.add((IFC[attr_name], RDF.type,  OWL.ObjectProperty))
        #define domain
        g.add((IFC[attr_name], RDFS.domain,  IFC[entity_name[3:]]))
        #add range to the attribute class
        range_name = IFC[type_of_attr.declared_type().name()[3:]]
        g.add((IFC[attr_name], RDFS.range,  range_name))
    
    elif type_of_attr.declared_type().as_select_type():
        items = type_of_attr.declared_type().select_list()
        applied = False
        applieds = 0
        for item in items:
            if item.as_entity():
                if item.name() not in ignore_entities: applied = True
                if applied:
                    applieds += 1
                    #as object property
                    g.add((IFC[attr_name], RDF.type,  OWL.ObjectProperty))
                    #define domain
                    g.add((IFC[attr_name], RDFS.domain,  IFC[entity_name[3:]]))
                    #add range to the attribute class
                    range_name = IFC[item.name()[3:]]
                    g.add((IFC[attr_name], RDFS.range,  range_name))
                applied = False

            elif item.as_type_declaration():
                applied = True
                applied+=1
                #as object property
                g.add((IFC[attr_name], RDF.type,  OWL.DatatypeProperty))
                #define domain
                g.add((IFC[attr_name], RDFS.domain,  IFC[entity_name[3:]]))
                #range to the attribute class
                range_name = type_maps[item.name()]
                g.add((IFC[attr_name], RDFS.range,  range_name))
        if applieds == 0 : return False
        
    elif type_of_attr.declared_type().as_enumeration_type(): #create  collection
        #as data property
        g.add((IFC[attr_name], RDF.type,  OWL.DatatypeProperty))

         #define domain
        g.add((IFC[attr_name], RDFS.domain,  IFC[entity_name[3:]]))

        range_name = XSD.string
        
        #add range to the attribute class
        g.add((IFC[attr_name], RDFS.range, range_name))

    else:
        #as object property
        g.add((IFC[attr_name], RDF.type,  OWL.DatatypeProperty))
        
        #define domain
        g.add((IFC[attr_name], RDFS.domain,  IFC[entity_name[3:]]))
        
        #range to the attribute class
        range_name = type_maps[type_of_attr.declared_type().name()]
        g.add((IFC[attr_name], RDFS.range,  range_name))
       
    #define as functional property
    g.add((IFC[attr_name], RDF.type,  OWL.FunctionalProperty))
    
    return True


#add ontology header triples
g.add((ref, RDF.type, OWL.Ontology))
g.add((ref, DCE.creator, Literal('Carlos Ramonell Cazador (carlos.ramonell@upc.edu)')))
g.add((ref, DCE.date, Literal('2024/03/27')))
g.add((ref, DCE.description, Literal("OWL ontology to describe processes in the built environment. It is based on the Proces ontology descibed in IFC (Insutry Foundation Classes) schema.")))
g.add((ref, DCE.identifier, Literal('Proces Ontology')))
g.add((ref, DCE.title, Literal('Proces Ontology')))
g.add((ref, DCE.language, Literal('en')))
g.add((ref, DCE.abstract, Literal(f"This Ontology is automatically created from the EXPRESS schema '{schema_name.upper()}' using the IFCExpress2OWL_Proces custom converter developed  by Carlos Ramonell (carlos.ramonell@upc.edu)")))
g.add((ref, VANN.preferredNamespaceUri, Literal(ref)))
g.add((ref, VANN.preferredNamespacePrefix, Literal('po')))
g.add((ref, CC.license, Literal('http://creativecommons.org/licenses/by/3.0/')))
g.add((ref, OWL.versionIRI, ref))
g.add((ref, OWL.versionInfo, Literal('1.0')))

# anotation properties
g.add((DCE.creator, RDF.type, OWL.AnnotationProperty))
g.add((DCE.contributor, RDF.type, OWL.AnnotationProperty))
g.add((DCE.date, RDF.type, OWL.AnnotationProperty))
g.add((DCE.title, RDF.type, OWL.AnnotationProperty))
g.add((DCE.description, RDF.type, OWL.AnnotationProperty))
g.add((DCE.identifier, RDF.type, OWL.AnnotationProperty))
g.add((DCE.language, RDF.type, OWL.AnnotationProperty))


# create empty list to filter different types of declarations
simple_types = {}
named_types = {}
aggregation_types = []
enumerations = []
selects = []
entities = []

#create  list of type_List to avoid list repetitions. Same for type_EmptyList
type_entities_List = []
type_entities_EmptyList = []

#add resources which entities are  going  to be ignored
avoid_resources =[
    'IfcGeometricConstraintResource',
    'IfcGeometricModelResource',
    'IfcGeometryResource',
    'IfcPresentationOrganizationResource',
    'IfcPresentationAppearanceResource',
    'IfcPresentationDefinitionResource',
    'IfcTopologyResource',
    'IfcRepresentationResource',
    'IfcExternalReferenceResource',
    'IfcStructuralLoadResource',
    'IfcConstraintResource',
    'IfcCostResource',
    'IfcApprovalResource',
    'IfcProfileResource',
    'IfcActorResource',
    'IfcMeasureResource',
    'IfcMaterialResource',
    'IfcUtilityResource'
]

resources_to_be_remade = [
    'IfcActorResource',
    'IfcMeasureResource'
]

avoid_domains  = [
    'IfcStructuralAnalysisDomain'
]

with open('./schema_structure/resources.json', 'r') as fp:
    resources =json.load(fp)

with open('./schema_structure/domain.json', 'r') as fp:
    domains =json.load(fp)

ignore_entities = [
    'IfcActor',
    'IfcAnnotation',
    'IfcAppliedValue',
    'IfcAsset',
    'IfcContext',
    'IfcControl',
    'IfcCostItem',
    'IfcCostSchedule',
    'IfcCivilElement',
    'IfcExternalSpatialStructureElement',
    'IfcFeatureElement',
    'IfcGroup',
    'IfcInventory',
    "IfcIrregularTimeSeries",
    "IfcIrregularTimeSeriesValue",
    'IfcLagTime',
    'IfcLinearElement',
    'IfcObject',
    'IfcObjectDefinition',
    'IfcPerformanceHistory',
    'IfcPermit',
    'IfcPort',
    'IfcProduct',
    'IfcPhysicalQuantity',
    'IfcProjectOrder',
    'IfcPropertyAbstraction',
    'IfcPropertyDefinition',
    'IfcPositioningElement',
    'IfcRecurrencePattern',
    'IfcRelationship',
    'IfcRelInterferesElements'
    "IfcRegularTimeSeries",
    'IfcResource',
    'IfcResourceLevelRelationship',
    'IfcResourceTime',
    'IfcRoot',
    'IfcTaskTimeRecurring',
    "IfcTimeSeries",
    "IfcTimeSeriesValue",
    'IfcTimePeriod',
    'IfcTypeObject',
    'IfcVirtualElement',    
	'IfcWorkCalendar',
    'IfcWorkTime'
]
ignore_attrs = [
    'OwnerHistory',
    'RefLatitude',
    'RefLongitude',
    'RefElevation',
    'ReferencedInStructures',
    'ContainedInStructure',
    'hasContext'
]
ignore_relations = [
            'IfcRelSpaceBoundary',
            'IfcRelInterferesElements',
            'IfcRelConnectsElements',
            'IfcRelConnectsWithRealizingElements',
            'IfcRelConnectsPorts'
            'IfcRelDefines',
            'IfcRelDefinesByObject',
            'IfcRelDefinesByProperties',
            'IfcRelDefinesByTemplate',
            'IfcRelDefinesByType'
        ]
type_maps = {}

# to ignores the resource entities  and types
if avoid_resources: 
    for resource in avoid_resources:
        ignore_entities += resources[resource]['Entities']

# to ignores the domain entities  and types
if avoid_domains: 
    for domain in avoid_domains:
        ignore_entities += domains[domain]['Entities']


# split the declarations of the schema to proceed to an ordered tranformation: first types, then entities.
for declaration in schema.declarations():
    
    if declaration.as_type_declaration():

        declared_type = declaration.declared_type()

        if declared_type.as_simple_type():
            type = declaration.declared_type().declared_type()
            if type == 'string': type = XSD.string
            elif type == 'real': type = XSD.float
            elif type == 'number': type = XSD.float
            elif type == 'boolean': type = XSD.boolean
            elif type == 'integer': type = XSD.integer
            elif type == 'logical': type = XSD.boolean
            elif type == 'binary': type = XSD.boolean
            else: print(type)
            type_maps[declaration.name()]= type

            
        elif declared_type.as_named_type():
            type = untangle_named_type_declaration(declaration).declared_type()
            if type == 'string': type = XSD.string
            elif type == 'real': type = XSD.float
            elif type == 'number': type = XSD.float
            elif type == 'boolean': type = XSD.boolean
            elif type == 'integer': type = XSD.integer
            elif type == 'logical': type = XSD.boolean
            elif type == 'binary': type = XSD.boolean
            else: print(type)
            type_maps[declaration.name()]=type
            
        elif declared_type.as_aggregation_type():
            aggregation_types.append(declaration)

        else: print('NOT IDENTIFIED TYPE: ' + str(declared_type))    
        

    elif declaration.as_select_type():
        pass
        
    elif declaration.as_enumeration_type():
        pass
    
    elif declaration.as_entity():
        entities.append(declaration)
    
    else: print('NOT IDENTIFIED DECLARATION: ' + str(declaration))

sub_ontology_root_name = 'IfcProcess'
root_supertypes = []
inverse_attributes ={}
for entity in entities:

    #create inverse attributes dictionary.
    if not entity.supertype():
        inverse_attributes[entity.name()]=[inv_attr.name() for inv_attr in entity.all_inverse_attributes()]
        iterate_subtypes_inverse_attrs(entity, inverse_attributes)

    #get collapsed supertypes for sub-ontologies
    if entity.name() == sub_ontology_root_name:
        root_supertypes = get_suertypes(entity)
    
    #ignore relations, types, and properties
    if is_supertype(entity, 'IfcRelationship'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
        
    elif is_supertype(entity, 'IfcTypeObject'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcPropertyDefinition'):
        if entity.name() not in ignore_entities: ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcPropertyAbstraction'):
        if entity.name() not in ignore_entities: ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcPositioningElement'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcResourceLevelRelationship'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcContext'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())

    elif is_supertype(entity, 'IfcLinearElement'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())

    elif is_supertype(entity, 'IfcTimeSeries'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcAppliedValue'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())

    elif is_supertype(entity, 'IfcPhysicalQuantity'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcResource'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcVirtualElement'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcFeatureElement'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcPort'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcExternalSpatialStructureElement'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcProduct'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
        
    elif is_supertype(entity, 'IfcActor'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())
    
    elif is_supertype(entity, 'IfcControl'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())

    elif is_supertype(entity, 'IfcGroup'):
        if entity.name() not in ignore_entities:ignore_entities.append(entity.name())

summary = {}
# Create entities
for entity  in entities:

    entity_name = entity.name()

    if  entity_name in ignore_entities:
        continue

    #store entity data
    if entity_name == sub_ontology_root_name:
        supertype =  None
        attrs = entity.all_attributes()
    else:
        supertype =  entity.supertype()
        attrs = entity.attributes()

    abstract = entity.is_abstract()
    derived =entity.derived()
    subtypes = [subtype.name() for subtype in entity.subtypes()]
    g.add((IFC[entity_name[3:]], RDF.type, OWL.Class))
    summary[entity.name()] = []
    
    #create dijsoint condition with all classes that share supertype
    if supertype: 
        g.add((IFC[entity_name[3:]], RDFS.subClassOf, IFC[supertype.name()[3:]]))
        disjoint = [subtype.name() for subtype in supertype.subtypes()]
        for disjoint_entity in disjoint: # ONE OF restriction in express applied to the subclasses of the superclass of the processed entity.
            if disjoint_entity != entity_name and disjoint_entity not in ignore_entities: g.add((IFC[entity_name[3:]], OWL.disjointWith, IFC[disjoint_entity[3:]]))

    # if it is an abstract supertype declare the class a subclass of the union of its subclasses (??)
    if abstract: 
        collection = []
        abstract_node = BNode()
        collection_node =BNode()
        item1 = collection_node
        item2 = BNode()
        
        for i  in range(len(subtypes)):
            if subtypes[i] not in ignore_entities:
                collection.append(subtypes[i])
        if len(collection) == 0: pass
        
        elif len(collection) == 1:            
            g.add((IFC[entity_name[3:]], RDFS.subClassOf, IFC[collection[0][3:]]))
        
        elif len(collection)> 1:
            for i in range(len(collection)):
                g.add((item1, RDF.first, IFC[collection[i][3:]]))
                g.add((item1, RDF.rest, item2))
                item1 = item2
                if i == len(collection)-2: item2 = RDF.nil
                else: item2 = BNode()

            g.add((abstract_node, RDF.type, OWL.Class))

            g.add((abstract_node, OWL.unionOf, collection_node))
            
            g.add((IFC[entity_name[3:]], RDFS.subClassOf, abstract_node))
    
    # Add attributes
    for attr in attrs:
        attr_label = attr.name()


        #if the attribute label is  already in the attr_ignore list, skip it.
        if attr_label in ignore_attrs:
            continue


        attr_name = attr_label[0].lower() + attr_label[1:] + '_' + entity_name[3:]
        type_of_attr = attr.type_of_attribute()
        optional = attr.optional()
        
        #If the attribute label is PredefinedType and leads to an Enum, extend the entity class creating as subclasses  the  enum items
        if attr_label == 'PredefinedType':continue 
                     
        if type_of_attr.as_simple_type():

            add_simple_type_attr(entity_name, attr_name, type_of_attr, optional)

        elif type_of_attr.as_named_type():

            if not add_named_type_attr(entity_name, attr_name, type_of_attr, optional): continue

        elif type_of_attr.as_aggregation_type():
            pass
            #if not add_aggregation_type_attr(entity_name, attr_name, type_of_attr, optional): continue
        
        #set label
        g.add((IFC[attr_name], RDFS.label,  Literal(attr_label)))
        if attr_label not in summary[entity.name()]: summary[entity.name()].append(attr_label)


    #add inverse attributes
    inv_attrs = entity.all_inverse_attributes()
    for inv_attr in inv_attrs:
        
        if inv_attr.name() in ignore_attrs:
            continue


        #only  process the inverse attributes assigned specifically to  the entity
        if inv_attr.name() in inverse_attributes[entity.name()]:

            
            inverse_attr_label = inv_attr.name()
            inverse_attr_name = inverse_attr_label[0].lower() + inverse_attr_label[1:] + '_' + entity_name[3:]
            bound1 = inv_attr.bound1()
            bound2 = inv_attr.bound2()

            if inv_attr.name() == 'OperatesOn':
                g.add((IFC[inverse_attr_name], RDF.type,  OWL.ObjectProperty))
                g.add((IFC[inverse_attr_name], RDFS.label,  Literal(inverse_attr_label)))
                g.add((IFC[inverse_attr_name], RDFS.domain,  IFC[entity_name[3:]]))
                continue


            reference_entity= inv_attr.entity_reference()

            if reference_entity.name() in ignore_relations: continue

            reference_entity_attrs = [item for item in reference_entity.all_attributes() if item.name() not in ['GlobalId','OwnerHistory', 'Name', 'Description', 'RelatedObjectsType', 'ActingRole', 'ConnectionGeometry', 'QuantityInProcess', 'SequenceType', 'TimeLag', 'UserDefinedSequenceType' ]]
            inverse_of_attr = inv_attr.attribute_reference()
            reference_entity_attr = None
                        
            if len(reference_entity_attrs) > 2: continue

            if len(reference_entity_attrs)==2:
                for ref_attr in reference_entity_attrs:
                    if inverse_of_attr.name() != ref_attr.name():
                        reference_entity_attr = ref_attr #this wont work well if the ref  entity has more than 2 attrs
            else: reference_entity_attr = None

            if reference_entity_attr:
                reference_entity_attr_type = reference_entity_attr.type_of_attribute()

                if reference_entity_attr_type.as_simple_type():
                    pass

                elif reference_entity_attr_type.as_named_type():
                    if reference_entity_attr_type.declared_type().as_entity():
                        ref_entity_name = reference_entity_attr_type.declared_type().name()

                        if ref_entity_name in ignore_entities:  
                            if ref_entity_name  in root_supertypes:
                                ref_entity_name = sub_ontology_root_name
                            else: continue

                        g.add((IFC[inverse_attr_name], RDF.type,  OWL.ObjectProperty))
                        g.add((IFC[inverse_attr_name], RDFS.label,  Literal(inverse_attr_label)))
                        g.add((IFC[inverse_attr_name], RDFS.domain,  IFC[entity_name[3:]]))
                        g.add((IFC[inverse_attr_name], RDFS.range,  IFC[ref_entity_name[3:]]))
                
                elif reference_entity_attr_type.as_aggregation_type():

                    type_of_element = reference_entity_attr_type.type_of_element()
                    
                    if type_of_element.declared_type().as_entity():
                        ref_entity_name = reference_entity_attr_type.type_of_element().declared_type().name()
                        
                        if ref_entity_name in ignore_entities:  
                            if ref_entity_name  in root_supertypes:
                                ref_entity_name = sub_ontology_root_name
                            else: continue

                        g.add((IFC[inverse_attr_name], RDF.type,  OWL.ObjectProperty))
                        g.add((IFC[inverse_attr_name], RDFS.label,  Literal(inverse_attr_label)))
                        g.add((IFC[inverse_attr_name], RDFS.domain,  IFC[entity_name[3:]]))
                        g.add((IFC[inverse_attr_name], RDFS.range,  IFC[ref_entity_name[3:]]))
                    
                    elif type_of_element.declared_type().as_select_type():
                        items= []
                        items = unnest_select(type_of_element.declared_type(), items)

                        for item in items:
                            if item.name() not in ignore_entities:
                                g.add((IFC[inverse_attr_name], RDF.type,  OWL.ObjectProperty))
                                g.add((IFC[inverse_attr_name], RDFS.label,  Literal(inverse_attr_label)))
                                g.add((IFC[inverse_attr_name], RDFS.domain,  IFC[entity_name[3:]]))
                                g.add((IFC[inverse_attr_name], RDFS.range,  IFC[item.name()[3:]]))
                            else:
                                if  item.name() in root_supertypes:
                                    g.add((IFC[inverse_attr_name], RDF.type,  OWL.ObjectProperty))
                                    g.add((IFC[inverse_attr_name], RDFS.label,  Literal(inverse_attr_label)))
                                    g.add((IFC[inverse_attr_name], RDFS.domain,  IFC[entity_name[3:]]))
                                    g.add((IFC[inverse_attr_name], RDFS.range,  IFC[sub_ontology_root_name[3:]]))

                    else:
                        pass

                if inverse_attr_label not in summary[entity.name()]: summary[entity.name()].append(inverse_attr_label)

#EXTENSION       
g.add((DOT.Inspection, RDFS.subClassOf, IFC.Task ))

path = 'ontos/'+schema_name.upper() +'_Processes'

g.serialize(destination= path + '.ttl', format ='turtle')

for item in summary.keys():  
    entity = schema.declaration_by_name(item)
    for supertype in get_suertypes(entity):
        if supertype in get_suertypes(schema.declaration_by_name(sub_ontology_root_name)):
            supertype = sub_ontology_root_name
        if supertype not in ignore_entities: summary[item] += summary[supertype]

with open('utils/ifc-ontologies/summary_'+ schema_name + '_processes.json',  'w') as fp:
    json.dump(summary,  fp, indent = 4)

with open('utils/ifc-ontologies/types_'+ schema_name + '_processes.json',  'w') as fp:
    json.dump(type_maps,  fp, indent = 4)
