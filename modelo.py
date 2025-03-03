import os
import pulp as pl

def solve_for_fixed_k(k, pedidos, itens, corredores, uoi, uai, LB, UB):
    prob = pl.LpProblem("WavePicking", pl.LpMaximize)
    
    # Variáveis binárias para seleção de pedidos e corredores
    x = {o: pl.LpVariable(f"x_{o}", cat='Binary') for o in pedidos}
    y = {a: pl.LpVariable(f"y_{a}", cat='Binary') for a in corredores}
    
    # Função objetivo: maximizar o número total de itens coletados.
    total_items = pl.lpSum(uoi[o][i] * x[o] for o in pedidos for i in itens[o])
    prob += total_items
    
    # Restrição: exatamente k corredores selecionados
    prob += pl.lpSum(y[a] for a in corredores) == k
    
    # Restrição de tamanho da wave
    prob += total_items >= LB
    prob += total_items <= UB
    
    # Restrição de disponibilidade de itens:
    todos_itens = set(i for o in pedidos for i in itens[o])
    for i in todos_itens:
        prob += pl.lpSum(uoi[o][i] * x[o] for o in pedidos if i in uoi[o]) <= \
                pl.lpSum(uai[a].get(i, 0) * y[a] for a in corredores)
    
    # Resolver o problema utilizando o solver CBC
    prob.solve(pl.PULP_CBC_CMD())
    
    return prob.status, pl.value(prob.objective), {o: pl.value(x[o]) for o in pedidos}, {a: pl.value(y[a]) for a in corredores}

def read_instance(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Primeira linha: número de pedidos (o), itens (i) e corredores (a)
    o, i, a = map(int, lines[0].split())
    pedidos = list(range(o))
    itens = {j: [] for j in pedidos}
    uoi = {j: {} for j in pedidos}
    
    # Leitura dos pedidos
    index = 1
    for j in range(o):
        data = list(map(int, lines[index].split()))
        index += 1
        k_items = data[0]
        for t in range(k_items):
            item, quantidade = data[1 + 2*t], data[2 + 2*t]
            itens[j].append(item)
            uoi[j][item] = quantidade
    
    # Leitura dos corredores
    corredores = list(range(a))
    uai = {b: {} for b in corredores}
    for b in range(a):
        data = list(map(int, lines[index].split()))
        index += 1
        l = data[0]
        for t in range(l):
            item, quantidade = data[1 + 2*t], data[2 + 2*t]
            uai[b][item] = quantidade
    
    # Leitura dos limites LB e UB
    LB, UB = map(int, lines[index].split())
    
    return pedidos, itens, corredores, uoi, uai, LB, UB

def save_output(file_path, best_obj, best_k, best_ratio, pedidos_selecionados, corredores_selecionados):
    with open(file_path, 'w') as f:
        f.write("Valor da função objetivo (total de itens): {}\n".format(best_obj))
        f.write("Número de corredores selecionados: {}\n".format(best_k))
        f.write("Relação (itens por corredor): {:.2f}\n".format(best_ratio))
        f.write("Número de pedidos na wave: {}\n".format(len(pedidos_selecionados)))
        f.write("Pedidos escolhidos:\n")
        for p in pedidos_selecionados:
            f.write("{}\n".format(p))
        f.write("Número de corredores na solução: {}\n".format(len(corredores_selecionados)))
        f.write("Corredores escolhidos:\n")
        for c in corredores_selecionados:
            f.write("{}\n".format(c))

def main():
    input_dir = "instances/"   # Pasta onde estão os arquivos de entrada
    output_dir = "results/"    # Pasta onde os resultados serão salvos
    os.makedirs(output_dir, exist_ok=True)
    
    # Lista e ordena os arquivos de entrada na ordem correta (instance_0001.txt a instance_0020.txt)
    files = sorted([f for f in os.listdir(input_dir) if f.startswith("instance_") and f.endswith(".txt")])
    
    for file_name in files:
        file_path = os.path.join(input_dir, file_name)
        pedidos, itens, corredores, uoi, uai, LB, UB = read_instance(file_path)
        
        best_ratio = -1
        best_solution = None
        best_k = None
        best_obj = None
        
        # Itera para k de 1 até o total de corredores disponíveis
        for k in range(1, len(corredores) + 1):
            status, obj_val, x_vals, y_vals = solve_for_fixed_k(k, pedidos, itens, corredores, uoi, uai, LB, UB)
            if status == pl.LpStatusOptimal:
                ratio = obj_val / k  # Itens coletados por corredor
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_solution = (x_vals, y_vals)
                    best_k = k
                    best_obj = obj_val
        
        if best_solution is not None:
            x_vals, y_vals = best_solution
            pedidos_selecionados = [o for o in pedidos if x_vals[o] == 1]
            corredores_selecionados = [a for a in corredores if y_vals[a] == 1]
            
            output_file = os.path.join(output_dir, file_name.replace(".txt", "_out.txt"))
            save_output(output_file, best_obj, best_k, best_ratio, pedidos_selecionados, corredores_selecionados)
            
            print("======================================")
            print(f"Arquivo processado: {file_name}")
            print(f"Valor da função objetivo (total de itens): {best_obj}")
            print(f"Número de corredores selecionados: {best_k}")
            print(f"Relação (itens por corredor): {best_ratio:.2f}")
            print("Pedidos escolhidos:", pedidos_selecionados)
            print("Corredores escolhidos:", corredores_selecionados)
            print("======================================\n")
        else:
            print(f"Arquivo processado: {file_name} - Nenhuma solução viável encontrada.\n")

if __name__ == "__main__":
    main()
