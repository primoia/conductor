# benchmarks/run_benchmark.py
import subprocess
import time
import statistics

# Comando a ser testado (um exemplo simples)
COMMAND = [
    "poetry", "run", "python", "src/cli/agent.py",
    "--env", "dev", "--proj", "test", "--agent", "BenchmarkAgent", "--input", "ping"
]
NUM_RUNS = 10

def run_benchmark():
    """Executa um comando CLI várias vezes e mede o tempo de execução."""
    timings = []
    print(f"Executando o comando {NUM_RUNS} vezes...")

    for i in range(NUM_RUNS):
        start_time = time.monotonic()
        # Assumindo que um agente mock 'BenchmarkAgent' existe para o teste
        subprocess.run(COMMAND, capture_output=True, text=True, check=True)
        end_time = time.monotonic()
        
        duration = end_time - start_time
        timings.append(duration)
        print(f"Execução {i+1}/{NUM_RUNS}: {duration:.4f} segundos")

    print("\n--- Resultados ---")
    print(f"Média: {statistics.mean(timings):.4f} segundos")
    print(f"Desvio Padrão: {statistics.stdev(timings):.4f} segundos")
    print(f"Mínimo: {min(timings):.4f} segundos")
    print(f"Máximo: {max(timings):.4f} segundos")

if __name__ == "__main__":
    run_benchmark()