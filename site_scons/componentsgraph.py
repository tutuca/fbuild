class ComponentsGraph(dict):
    """
    Keeps track of registered components.
    Checks that components are not registered twice.
    There should be only one instance (Singleton).
    """
    def __setitem__(self, key, component, check=True):
        if check:
            if not component.name.islower():
                component.env.Cprint(
                    '[warn] modules names should be lower case: {}'.format(component.name), 
                    'yellow')
        # Its possible that a component is tried to be added twice because a new
        # dependency was downloaded and
        if key not in self:
            self[key] = component
            return component
        else:
            component.env.Cprint(
                '[warn] component tried to be re-added {}'.format(key), 
                'yellow')