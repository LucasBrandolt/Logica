from pysat.solvers import Glucose4

import sys
from instance_manager.satplan_instance import SatPlanInstance, SatPlanInstanceMapper
import time
comeco = time.time()

def create_literal_for_level(level, literal):
    pure_atom = literal.replace("~","")
    return f"~{level}_{pure_atom}" if literal[0] == "~" else f"{level}_{pure_atom}"

def create_literals_for_level_from_list(level, literals):
    return [create_literal_for_level(level, literal) for literal in literals]

def create_state_from_true_atoms(true_atoms, all_atoms):
    initial_state = [f"~{atom}" for atom in all_atoms if atom not in true_atoms]
    return true_atoms + initial_state

def create_state_from_literals(literals, all_atoms):
    positive_literals = [literal for literal in literals if literal[0] != "~"]
    return create_state_from_true_atoms(positive_literals, all_atoms)

def formatar_tempo(tempo_total):
    horas, restante = divmod(tempo_total, 3600)
    minutos, segundos = divmod(restante, 60)
    
    # Arredondar os segundos para 3 casas decimais
    segundos = round(segundos, 3)

    return int(horas), int(minutos), segundos

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python your_script.py <filename>")
        sys.exit(1)      

    satPlanInstance = SatPlanInstance(sys.argv[1])
    instanceMapper  = SatPlanInstanceMapper()
    
    tempo_maximo = 100
    for passo in range(1, tempo_maximo):
        solver = Glucose4()
        count_literals = 0
        count_clauses = 0
        print(f'Passo: {passo}')
        all = []
        #Ação 1_0, Ação 1_1, Ação 1_2... 
        for i in range(passo): # Laço principal
            # Ranya part
            state_atoms = satPlanInstance.get_state_atoms() # Não são ações 
            #on_c_d
            #clear_a
            state_0 = create_literals_for_level_from_list(0, state_atoms) 
            #0_on_c_d
            #0_clear_a
            instanceMapper.add_list_of_literals_to_mapping(state_0)
            # Ex: ~on_d_c = -4
            
            initial_state = create_literals_for_level_from_list(0, satPlanInstance.get_initial_state())
            # Literais do estado inicial [0_clear_a, 0_clear_b]
            negative_literais = [i for i in state_0 if i not in initial_state]

            # Todos os átomos de estado que estão no estado inicial
            for literal in initial_state: # Todos os literais do estado inicial são verdadeiros
                solver.add_clause([instanceMapper.get_literal_from_mapping(f'{literal}')]) # Passando unitário [4]
                count_literals += 1  # [2] verdade
                count_clauses +=1
            
            for literal in negative_literais: # Todos os literais do estado que não estão em initial_state
                solver.add_clause([instanceMapper.get_literal_from_mapping(f'~{literal}')])# Passando unitário e negativo
                count_literals += 1 # [-2] falso
                count_clauses +=1
                #fim Ranya
                #estado inicial  verdadeiro/ Falso *
                #pré-condições  *
                #pós-condições  *
                #perpetuação de estado
                #estado final

                actions = create_literals_for_level_from_list(i, satPlanInstance.get_actions())
                
                all.extend(actions)
                
                instanceMapper.add_list_of_literals_to_mapping(actions)

                solver.add_clause(instanceMapper.get_list_of_literals_from_mapping(actions))
                count_literals += len(actions)
                count_clauses += 1

            for action in satPlanInstance.get_actions():            
                action_level = create_literal_for_level(i, action)

                precondition_no_level = satPlanInstance.get_action_preconditions(action)
                poscondition_no_level = satPlanInstance.get_action_posconditions(action)

                preconditions = create_literals_for_level_from_list(i, precondition_no_level)
                posconditions = create_literals_for_level_from_list(i + 1, poscondition_no_level)

                for action_j in satPlanInstance.get_actions():
                    action_j_level = create_literal_for_level(i, action_j)
                    
                    if action_j_level != action_level:
                        solver.add_clause(instanceMapper.get_list_of_literals_from_mapping([f'~{action_j_level}', f'~{action_level}']))
                        count_literals += 2
                        count_clauses += 1

                instanceMapper.add_list_of_literals_to_mapping(preconditions)
                instanceMapper.add_list_of_literals_to_mapping(posconditions)
                #Henry
                for precondition in preconditions:
                    solver.add_clause([instanceMapper.get_literal_from_mapping(f'~{action_level}'), instanceMapper.get_literal_from_mapping(precondition)]) #[~ação, pré]
                    count_literals += 2  
                    count_clauses += 1

                for poscondition in posconditions:
                    solver.add_clause([instanceMapper.get_literal_from_mapping(f'~{action_level}'), instanceMapper.get_literal_from_mapping(poscondition)]) #[~ação, pos]
                    count_literals += 2
                    count_clauses += 1
                #fim henry
                for state_atom in state_atoms:
                    if state_atom not in poscondition_no_level and f'~{state_atom}' not in poscondition_no_level:

                        state_atom_i = create_literal_for_level(i, state_atom)
                        state_atom_i_plus_1 = create_literal_for_level(i + 1, state_atom)

                        instanceMapper.add_list_of_literals_to_mapping([state_atom, state_atom_i_plus_1])
                        
                        solver.add_clause(instanceMapper.get_list_of_literals_from_mapping([f'~{action_level}', f'~{state_atom_i}', state_atom_i_plus_1]))
                        solver.add_clause(instanceMapper.get_list_of_literals_from_mapping([f'~{action_level}', f'{state_atom_i}' , f'~{state_atom_i_plus_1}']))
                        count_literals += 6
                        count_clauses += 2 


        final_state = create_literals_for_level_from_list(passo, satPlanInstance.get_final_state())
                
        instanceMapper.add_list_of_literals_to_mapping(final_state)
        
        for literal in final_state:
            solver.add_clause([instanceMapper.get_literal_from_mapping(literal)])
            count_literals += 1
            count_clauses += 1

        solver.solve()
        if type(solver.get_model()) == list: #None
            print("-------------------------------------")
            print(f'Funcionou com {passo} passos')
        else: 
            continue
        
        print("-------------  sequencia de Ações  ---------------------")
        for valor in solver.get_model(): #valor inteiro
            lit = instanceMapper.get_literal_from_mapping_reverse(valor) #lit string
            
            if lit in all:
                print(lit)
            
        break
    
    
    final = time.time()
    tempo_total = final - comeco
    
    horas, minutos, segundos = formatar_tempo(tempo_total)
    print(f'Tempo necessário para finalizar a execução: {horas} horas, {minutos} minutos e {segundos} segundos')
    print(f'Quantidade de clausulas: {count_clauses}')
    print(f'Quantidade de literais: {count_literals}')
