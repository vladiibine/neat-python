import sys
from neat.math_util import mean


def species_max_fitness(species):
    return max([m.fitness for m in species.members])


def species_min_fitness(species):
    return min([m.fitness for m in species.members])


def species_mean_fitness(species):
    return mean([m.fitness for m in species.members])


def species_median_fitness(species):
    fitnesses = [m.fitness for m in species.members]
    fitnesses.sort()
    return fitnesses[len(fitnesses) // 2]


# TODO: Add a method for the user to change the "is stagnant" computation.

class DefaultStagnation(object):
    def __init__(self, config, reporters):
        params = config.get_type_config(self)

        self.max_stagnation = int(params.get('max_stagnation'))
        self.species_fitness = params.get('species_fitness_func')
        self.species_elitism = int(params.get('species_elitism'))

        if self.species_fitness == 'max':
            self.species_fitness_func = species_max_fitness
        elif self.species_fitness == 'min':
            self.species_fitness_func = species_min_fitness
        elif self.species_fitness == 'mean':
            self.species_fitness_func = species_mean_fitness
        elif self.species_fitness == 'median':
            self.species_fitness_func = species_median_fitness
        else:
            raise Exception("Unexpected species fitness: {0!r}".format(self.species_fitness))

        self.reporters = reporters

        self.previous_fitnesses = {}
        self.stagnant_counts = {}

    def remove(self, species):
        if species.ID in self.previous_fitnesses:
            del self.previous_fitnesses[species.ID]

        if species.ID in self.stagnant_counts:
            del self.stagnant_counts[species.ID]

    def update(self, species):
        result = []
        every_fitness = set()
        species_fitness_stagnant = {}  # {species: [fitness, is_stagnant]}

        # Calculate the fitness value, and whether the species stagnated
        for s in species:
            fitness = self.species_fitness_func(s)
            scount = self.stagnant_counts.get(s.ID, 0)
            prev_fitness = self.previous_fitnesses.get(s.ID, -sys.float_info.max)
            if fitness > prev_fitness:
                scount = 0
            else:
                scount += 1

            every_fitness.add(fitness)

            self.previous_fitnesses[s.ID] = fitness
            self.stagnant_counts[s.ID] = scount

            is_stagnant = scount >= self.max_stagnation
            species_fitness_stagnant[species] = [fitness, is_stagnant]

        # Save the elite species from removal (set their is_stagnant to False)
        elite_fitness_values = \
            set(sorted(every_fitness, reverse=True)[:self.species_elitism])
        elites_saved = 0
        for s, fitness_stagnant in species_fitness_stagnant.items():
            fitness, is_stagnant = fitness_stagnant

            if (is_stagnant and fitness in elite_fitness_values and
                        elites_saved < self.species_elitism):
                    elites_saved += 1
                    fitness_stagnant[1] = False

        # Remove the remaining stagnant species, and construct the result
        for s, fitness_stagnant in species_fitness_stagnant.items():
            fitness, is_stagnant = fitness_stagnant

            if is_stagnant:
                self.remove(s)

            is_elite = fitness in elite_fitness_values
            result.append((s, is_stagnant, is_elite))

        self.reporters.info('Species no improv: {0!r}'.format(self.stagnant_counts))

        return result
