
class Generator():
	def __init__(self, label, capacity_MW):
		self.capacity_MW = capacity_MW
		self.current_output_MW = 0
		self.label = label
		self.type_idx = 0
	
	def get_minimum_next_output_MWh(self, time_step_mins):
		return 0

	def get_maximum_next_output_MWh(self, time_step_mins):
		return self.current_output + 1

	def get_srmc(self):
		return np.float32(0)
	
	def get_lrmc(self):
		return np.float32(0)

	

class Coal_Generator(Generator):
	def __init__(self, label, capacity_MW, ramp_rate_MW_per_min, srmc, lrmc):
		Generator.__init__(self, label, capacity_MW)
		self.ramp_rate_MW_per_min = ramp_rate_MW_per_min
		self.srmc = srmc
		self.lrmc = lrmc
		self.current_output_MW = capacity_MW
		self.type_idx = 1

	def get_minimum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping down.
		next_output = next_output - 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output is below zero, we just return 0
		return max(next_output, 0)

	def get_maximum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping up.
		next_output = next_output + 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output above the capacity, we just return the energy generated at capacity
		return min(next_output, float(self.capacity_MW) * float(time_step_mins) / 60.0)

	def get_srmc(self):
		return np.float32(self.srmc)

	def get_lrmc(self):
		return np.float32(self.lrmc)

	def set_output_MW(self, MW, time_step_mins):
		maximum = self.get_maximum_next_output_MWh(time_step_mins)
		minimum = self.get_minimum_next_output_MWh(time_step_mins)
		if MW > maximum:
			self.current_output_MW = maximum * 60.0 / time_step_mins
		elif MW < minimum:
			self.current_output_MW = minimum * 60.0 / time_step_mins
		else:
			self.current_output_MW = MW

class Gas_Turbine_Generator(Generator):
	def __init__(self, label, capacity_MW, ramp_rate_MW_per_min, srmc, lrmc):
		Generator.__init__(self, label, capacity_MW)
		self.ramp_rate_MW_per_min = ramp_rate_MW_per_min
		self.srmc = srmc
		self.lrmc = lrmc
		self.type_idx = 2

	def get_minimum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping down.
		next_output = next_output - 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output is below zero, we just return 0
		return max(next_output, 0)

	def get_maximum_next_output_MWh(self, time_step_mins):
		# Calculate the maximum output power change.
		maximum_change_MW = float(time_step_mins) * float(self.ramp_rate_MW_per_min)
		# Calculate output if kept steady.
		next_output = float(self.current_output_MW) *  float(time_step_mins) / 60.0
		# Triangle calc to take into account ramping up.
		next_output = next_output + 0.5 * float(maximum_change_MW) * float(time_step_mins) / 60.0
		# Make sure if next min output above the capacity, we just return the energy generated at capacity
		return min(next_output, float(self.capacity_MW) * float(time_step_mins) / 60.0)

	def get_srmc(self):
		return np.float32(self.srmc)

	def get_lrmc(self):
		return np.float32(self.lrmc)
