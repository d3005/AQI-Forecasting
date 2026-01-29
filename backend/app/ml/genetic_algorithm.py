"""
Genetic Algorithm for KELM Hyperparameter Optimization

Optimizes KELM parameters:
- C: Regularization parameter
- gamma: RBF kernel coefficient

Uses:
- Tournament selection
- Blend crossover (BLX-α) for continuous parameters
- Gaussian mutation
- Elitism to preserve best solutions

Reference:
Goldberg, D.E. (1989). Genetic Algorithms in Search, Optimization, 
and Machine Learning. Addison-Wesley.
"""

import numpy as np
from typing import Tuple, List, Callable, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """Represents an individual in the population (set of hyperparameters)"""
    genes: np.ndarray  # [C, gamma]
    fitness: float = float('-inf')
    
    @property
    def C(self) -> float:
        return self.genes[0]
    
    @property
    def gamma(self) -> float:
        return self.genes[1]


class GeneticAlgorithm:
    """
    Genetic Algorithm optimizer for KELM hyperparameters.
    
    Finds optimal C and gamma values to minimize validation error.
    
    Attributes:
        population_size: Number of individuals in population
        generations: Maximum number of generations
        mutation_rate: Probability of mutation (0-1)
        crossover_rate: Probability of crossover (0-1)
        elitism_count: Number of best individuals to preserve
        tournament_size: Size of tournament for selection
    """
    
    # Parameter bounds
    C_BOUNDS = (0.01, 1000.0)       # Regularization parameter
    GAMMA_BOUNDS = (0.001, 10.0)    # RBF kernel coefficient
    
    def __init__(
        self,
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elitism_count: int = 2,
        tournament_size: int = 3,
        early_stopping_rounds: int = 10,
        random_state: Optional[int] = None,
    ):
        """
        Initialize Genetic Algorithm.
        
        Args:
            population_size: Size of population
            generations: Maximum generations to evolve
            mutation_rate: Mutation probability
            crossover_rate: Crossover probability
            elitism_count: Number of elites to preserve
            tournament_size: Tournament selection size
            early_stopping_rounds: Stop if no improvement
            random_state: Random seed for reproducibility
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_count = elitism_count
        self.tournament_size = tournament_size
        self.early_stopping_rounds = early_stopping_rounds
        
        if random_state is not None:
            np.random.seed(random_state)
        
        # Tracking
        self.best_individual: Optional[Individual] = None
        self.fitness_history: List[float] = []
        self.generation_stats: List[dict] = []
    
    def _initialize_population(self) -> List[Individual]:
        """
        Initialize population with random individuals.
        Uses log-uniform distribution for better coverage.
        """
        population = []
        
        for _ in range(self.population_size):
            # Log-uniform sampling for C and gamma
            log_c = np.random.uniform(
                np.log10(self.C_BOUNDS[0]), 
                np.log10(self.C_BOUNDS[1])
            )
            log_gamma = np.random.uniform(
                np.log10(self.GAMMA_BOUNDS[0]), 
                np.log10(self.GAMMA_BOUNDS[1])
            )
            
            genes = np.array([10**log_c, 10**log_gamma])
            population.append(Individual(genes=genes))
        
        return population
    
    def _evaluate_fitness(
        self, 
        individual: Individual,
        fitness_func: Callable[[float, float], float]
    ) -> float:
        """
        Evaluate fitness of an individual.
        
        Args:
            individual: Individual to evaluate
            fitness_func: Function that returns negative MSE given (C, gamma)
            
        Returns:
            Fitness score (higher is better)
        """
        try:
            fitness = fitness_func(individual.C, individual.gamma)
            return fitness
        except Exception as e:
            logger.warning(f"Fitness evaluation failed for C={individual.C}, gamma={individual.gamma}: {e}")
            return float('-inf')
    
    def _tournament_selection(self, population: List[Individual]) -> Individual:
        """
        Select individual using tournament selection.
        
        Randomly selects tournament_size individuals and returns the best.
        """
        tournament = np.random.choice(
            population, 
            size=min(self.tournament_size, len(population)),
            replace=False
        )
        return max(tournament, key=lambda x: x.fitness)
    
    def _blend_crossover(
        self, 
        parent1: Individual, 
        parent2: Individual,
        alpha: float = 0.5
    ) -> Tuple[Individual, Individual]:
        """
        Blend crossover (BLX-α) for continuous parameters.
        
        Creates offspring in expanded range between parents.
        """
        if np.random.random() > self.crossover_rate:
            return Individual(genes=parent1.genes.copy()), Individual(genes=parent2.genes.copy())
        
        child1_genes = np.zeros(2)
        child2_genes = np.zeros(2)
        
        for i in range(2):
            min_val = min(parent1.genes[i], parent2.genes[i])
            max_val = max(parent1.genes[i], parent2.genes[i])
            range_val = max_val - min_val
            
            # Expand range by alpha
            low = min_val - alpha * range_val
            high = max_val + alpha * range_val
            
            # Clip to bounds
            bounds = self.C_BOUNDS if i == 0 else self.GAMMA_BOUNDS
            low = max(low, bounds[0])
            high = min(high, bounds[1])
            
            child1_genes[i] = np.random.uniform(low, high)
            child2_genes[i] = np.random.uniform(low, high)
        
        return Individual(genes=child1_genes), Individual(genes=child2_genes)
    
    def _gaussian_mutation(self, individual: Individual) -> Individual:
        """
        Apply Gaussian mutation to individual.
        
        Adds Gaussian noise to parameters with probability mutation_rate.
        """
        new_genes = individual.genes.copy()
        
        for i in range(2):
            if np.random.random() < self.mutation_rate:
                bounds = self.C_BOUNDS if i == 0 else self.GAMMA_BOUNDS
                
                # Mutation in log space for better exploration
                log_val = np.log10(new_genes[i])
                log_bounds = (np.log10(bounds[0]), np.log10(bounds[1]))
                
                # Gaussian noise proportional to range
                std = (log_bounds[1] - log_bounds[0]) * 0.1
                log_val += np.random.normal(0, std)
                
                # Clip and convert back
                log_val = np.clip(log_val, log_bounds[0], log_bounds[1])
                new_genes[i] = 10**log_val
        
        return Individual(genes=new_genes)
    
    def evolve(
        self,
        fitness_func: Callable[[float, float], float],
        verbose: bool = True
    ) -> Tuple[float, float]:
        """
        Run genetic algorithm optimization.
        
        Args:
            fitness_func: Function that takes (C, gamma) and returns 
                         negative MSE (or other metric where higher is better)
            verbose: Whether to log progress
            
        Returns:
            Tuple of (best_C, best_gamma)
        """
        # Initialize population
        population = self._initialize_population()
        
        # Evaluate initial fitness
        for individual in population:
            individual.fitness = self._evaluate_fitness(individual, fitness_func)
        
        # Track best
        self.best_individual = max(population, key=lambda x: x.fitness)
        self.fitness_history = [self.best_individual.fitness]
        
        no_improvement_count = 0
        
        for generation in range(self.generations):
            # Sort by fitness (descending)
            population.sort(key=lambda x: x.fitness, reverse=True)
            
            # Create new population
            new_population = []
            
            # Elitism: preserve best individuals
            for i in range(self.elitism_count):
                new_population.append(Individual(genes=population[i].genes.copy()))
            
            # Generate rest of population
            while len(new_population) < self.population_size:
                # Selection
                parent1 = self._tournament_selection(population)
                parent2 = self._tournament_selection(population)
                
                # Crossover
                child1, child2 = self._blend_crossover(parent1, parent2)
                
                # Mutation
                child1 = self._gaussian_mutation(child1)
                child2 = self._gaussian_mutation(child2)
                
                new_population.extend([child1, child2])
            
            # Trim to population size
            population = new_population[:self.population_size]
            
            # Evaluate fitness
            for individual in population:
                if individual.fitness == float('-inf'):
                    individual.fitness = self._evaluate_fitness(individual, fitness_func)
            
            # Update best
            current_best = max(population, key=lambda x: x.fitness)
            
            if current_best.fitness > self.best_individual.fitness:
                self.best_individual = Individual(
                    genes=current_best.genes.copy(),
                    fitness=current_best.fitness
                )
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            self.fitness_history.append(self.best_individual.fitness)
            
            # Statistics
            fitnesses = [ind.fitness for ind in population if ind.fitness > float('-inf')]
            stats = {
                'generation': generation + 1,
                'best_fitness': self.best_individual.fitness,
                'mean_fitness': np.mean(fitnesses) if fitnesses else 0,
                'std_fitness': np.std(fitnesses) if fitnesses else 0,
                'best_C': self.best_individual.C,
                'best_gamma': self.best_individual.gamma,
            }
            self.generation_stats.append(stats)
            
            if verbose and (generation + 1) % 10 == 0:
                logger.info(
                    f"Generation {generation + 1}: "
                    f"Best Fitness = {self.best_individual.fitness:.6f}, "
                    f"C = {self.best_individual.C:.4f}, "
                    f"gamma = {self.best_individual.gamma:.6f}"
                )
            
            # Early stopping
            if no_improvement_count >= self.early_stopping_rounds:
                if verbose:
                    logger.info(f"Early stopping at generation {generation + 1}")
                break
        
        return self.best_individual.C, self.best_individual.gamma
    
    def get_optimization_summary(self) -> dict:
        """Get summary of optimization run"""
        return {
            'best_C': self.best_individual.C if self.best_individual else None,
            'best_gamma': self.best_individual.gamma if self.best_individual else None,
            'best_fitness': self.best_individual.fitness if self.best_individual else None,
            'generations_run': len(self.fitness_history),
            'fitness_history': self.fitness_history,
            'population_size': self.population_size,
        }
