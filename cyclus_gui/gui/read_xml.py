import xmltodict


def read_xml(path, which):
    with open(path, 'r') as f:
        obj = xmltodict.parse(f.read())

    n = 0


    if which == 'recipe':
        recipe_dict = {}
        xml_list = check_list(obj['root']['recipe'])
        for recipe in xml_list:
            n += 1
            comp_dict = {}
            if not isinstance(recipe['nuclide'], list):
                recipe['nuclide'] = [recipe['nuclide']]
            for entry in recipe['nuclide']:
                comp_dict[entry['id']] = entry['comp']
            recipe_dict[recipe['name']] = {'base': recipe['basis'],
                                           'composition': comp_dict}
        return recipe_dict, n



    if which == 'arche':
        new_arche = []
        xml_dict = obj['archetypes']
        for entry in xml_dict['spec']:
            new_arche.append([entry['lib'], entry['name']])
            n += 1
        return new_arche, n



    if which == 'region':
        region_dict = {}
        xml_list = check_list(obj['root']['region'])
        proto_dict, arche, w = read_xml(path.replace('region.xml', 'facility.xml'), 'facility')

        for region in xml_list:
            region_dict[region['name']] = {}

            region['institution'] = check_list(region['institution'])

            for i in region['institution']:
                inst_array = []
                if 'DeployInst' in i['config'].keys():
                    print(i['config'])
                    prototypes = i['config']['DeployInst']['prototypes']['val']
                    instname = i['name']

                    prototypes = check_list(prototypes)

                    for indx, p in enumerate(prototypes):
                        n += 1
                        entry_list = []
                        entry_dict = i['config']['DeployInst']
                        for cat in ['prototypes', 'n_build', 'build_times', 'lifetimes']:
                            if len(prototypes) == 1:
                                entry_list.append(entry_dict[cat]['val'])
                            else:
                                entry_list.append(entry_dict[cat]['val'][indx])
                        inst_array.append(entry_list)


                if 'initialfacilitylist' in i.keys():
                    instname = i['name']
                    print(i)
                    init_facility = i['initialfacilitylist']['entry']
                    init_facility = check_list(init_facility)
                    for i in init_facility:
                        n += 1
                        entry_list = [i['prototype'], i['number'], '1', '99999']
                        if 'lifetime' in proto_dict[i['prototype']].keys():
                            entry_list[3] = proto_dict[i['prototype']]['lifetime']
                        inst_array.append(entry_list)
            region_dict[region['name']][instname] = inst_array

        return region_dict, n


    if which == 'facility':
        proto_dict = {}
        arche_dict = {}
        xml_list = check_list(obj['root']['facility'])
        for facility in xml_list:
            n += 1
            facility_name = facility['name']
            archetype = list(facility['config'].keys())[0]
            proto_dict[facility_name] = {'archetype': archetype,
                                         'config':{archetype: facility['config'][archetype]}}
            if 'lifetime' in facility.keys():
                proto_dict[facility_name]['lifetime'] = facility['lifetime']
            # default is cycamore - do something about this
            arche_dict[facility_name] = archetype

        new_dict = {}
        arches, w = read_xml(path.replace('facility.xml', 'archetypes.xml'), 'arche')
        for facname, archename in arche_dict.items():
            matcher = []
            for i in arches:
                if archename in i[1]:
                    matcher.append(i[0])

            if len(matcher) == 1:
                libname = matcher[0]
            elif len(matcher) != 1 and 'cycamore' in matcher:
                libname = 'cycamore'
            else:
                raise ValueError('duplicate names?')

            new_dict[facname] = libname + ':' + archename

        arche_dict = new_dict

        return proto_dict, arche_dict, n



def check_list(o):
    # this function is used since
    # having one entry in an xml tree
    # returns a dictionary or string, not a list
    if not isinstance(o, list):
        return [o]
    else:
        return o


        
