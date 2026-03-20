import copy

class WorldCupCSP:
    def __init__(self, teams, groups, debug=False):
        """
        Inicializa el problema CSP para el sorteo del Mundial.
        :param teams: Diccionario con los equipos, sus confederaciones y bombos.
        :param groups: Lista con los nombres de los grupos (A-L).
        :param debug: Booleano para activar trazas de depuración.
        """
        self.teams = teams
        self.groups = groups
        self.debug = debug

        # Las variables son los equipos.
        self.variables = list(teams.keys())

        # El dominio de cada variable inicialmente son todos los grupos.
        self.domains = {team: list(groups) for team in self.variables}

    def get_team_confederation(self, team):
        return self.teams[team]["conf"]

    def get_team_pot(self, team):
        return self.teams[team]["pot"]

    def is_valid_assignment(self, group, team, assignment):
        """
        Verifica si asignar un equipo a un grupo viola
        las restricciones de confederación o tamaño del grupo.
        """
        teams_in_group = [t for t, g in assignment.items() if g == group]

        # Restricción de tamaño del grupo
        if len(teams_in_group) >= 4:
            return False
        
        #Restriccion de un solo equipo por bombo
        team_pot = self.get_team_pot(team)
        for t in teams_in_group:
            if self.get_team_pot(t) == team_pot:
                return False
            
        #Restriccion por confederacion
        team_conf = self.get_team_confederation(team)
        conf_count = {}
        playoff_inter_confs = set()

        for t in teams_in_group:
            t_conf = self.get_team_confederation(t)
            if isinstance(t_conf, list):
                playoff_inter_confs.update(t_conf)
            else:
                conf_count[t_conf] = conf_count.get(t_conf, 0) + 1

        if isinstance(team_conf, list):
            return True
        
        current = conf_count.get(team_conf, 0)
        if team_conf == "UEFA":
            #Maximo 2 por grupo para UEFA
            return current < 2
        else:
            limit = 2 if team_conf in playoff_inter_confs else 1
            return current < limit

    def forward_check(self, assignment, domains):
        """
        Propagación de restricciones.
        Debe eliminar valores inconsistentes en dominios futuros.
        Retorna True si la propagación es exitosa, False si algún dominio queda vacío.
        """
        # Hacemos una copia de los dominios actuales para modificarla de forma segura
        new_domains = copy.deepcopy(domains)

        for var in self.variables:
            if var not in assignment:
                new_domains[var] = [
                    g for g in new_domains[var]
                    if self.is_valid_assignment(g, var, assignment)
                ]

                if len(new_domains[var]) == 0:
                    if self.debug:
                        print(f"[Forward Check] Dominio vacío para {var} - forzando backtrack.")
                    return False, new_domains
                
        return True, new_domains

    def select_unassigned_variable(self, assignment, domains):
        """
        Heurística MRV (Minimum Remaining Values).
        Selecciona la variable no asignada con el dominio más pequeño.
        """
        unassigned_vars = [v for v in self.variables if v not in assignment]
        if not unassigned_vars:
            return None
        
        return min(unassigned_vars, key = lambda v: len(domains[v]))

    def backtrack(self, assignment, domains=None):
        """
        Backtracking search para resolver el CSP.
        """
        if assignment is None:
            assignment = {}

        if domains is None:
            domains = copy.deepcopy(self.domains)

        # Condición de parada: Si todas las variables están asignadas, retornamos la asignación.
        if len(assignment) == len(self.variables):
            return assignment

        # 1. Seleccionar variable con MRV
        var = self.select_unassigned_variable(assignment, domains)
        if var is None:
            return None
        
        if self.debug:
            print(f"Seleccionada variable: {var} con dominio {domains[var]}")

        # 2. Iterar sobre sus valores (grupos) posibles en el dominio
        for value in domains[var]:
            if not self.is_valid_assignment(value, var, assignment):
                continue
        
        # 3. Verificar si es válido, hacer la asignación y aplicar forward checking
            assignment[var] = value
            if self.debug:
                print(f"Asignando {var} -> {value}. Asignación actual: {assignment}")

        # 4. Llamada recursiva
            success, new_domains = self.forward_check(assignment, domains)

            if success:
                result = self.backtrack(assignment, new_domains)
                if result is not None:
                    return result
                
        # 5. Deshacer la asignación si falla (backtrack)
            if self.debug:
                print(f"Backtracking: Deshaciendo {var} -> {value}.")
            del assignment[var]

        return None
