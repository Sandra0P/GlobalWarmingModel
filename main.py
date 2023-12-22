import random
import numpy as np

from PIL import Image, ImageTk
import PIL
import tkinter as tk
import csv
import os

UPDATE_TIME = 2000 #2 seconds
AIR_POLLUTION_AVERAGE = 0
GLOBAL_WARMING_STATE_A = 0
GLOBAL_WARMING_STATE_B =0


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.element = random.choice(["earth", "water", "forest", "city"]) #ice element also exists, but cannot be randomly chosen
        if self.element == "city":
            self.air_pollution = int(self.get_air_pollution())
        else:
            self.air_pollution = self.decrease_by_percentage(self.get_air_pollution(), 50) #very little air pollution to start with if its not a city
        self.cloud = random.choice(["cloud", "rain cloud", "cloudless"]) #either 'cloud', 'rain cloud' or None
        self.wind_force = random.randint(1,50)
        self.wind_direction = random.choice(["N", "E", "W", "S"]) #from N, E, W, S
        self.temperature = self.define_temp()
        self.raining = False


    def define_temp(self):
        #used for initial temperature declaration
        if self.element == "earth":
            return 25
        if self.element == "water":
            return 15
        if self.element == "ice":
            return -20
        if self.element == "forest":
            return 20
        if self.element == "city":
            return 27

    def update_element(self, new_element):
        #used to change the element of the cell
        self.element = new_element
        self.temperature = self.define_temp()


    def apply_rules(self, map_matrix):
        """rules:
        air pollution increases temperature
        strong winds should decrease air pollution in current element
        forests should eat up some of the air pollution
        if element is city, check todays average air pollution and increase current air pollution by it

        use wind force and wind direction to apply air pollution on neighbor cells
        wind force in current cell naturally decreases, and in neighbor cell increases

        rain calculation: chances of rain depend on region , temperature, wind force and the cloud needs to be rain cloud. if it didn't rain - move rain cloud to neighbor
        in cloudless cell which is sea - generate rain clouds

        if temperature is above a certain level and element is ice - make it water
        """

        #calculate my air pollution
        if self.element == "forest": #decreae air pollution in forests
            # self.air_pollution = self.decrease_by_percentage(self.air_pollution, 50/100) #default
            self.air_pollution = self.decrease_by_percentage(self.air_pollution, 10)
        elif self.element == "city": #increase air pollution in cities
            self.air_pollution += 0.01*random.uniform(AIR_POLLUTION_AVERAGE-0.05, AIR_POLLUTION_AVERAGE+0.05)
        if self.wind_force > 70: #if wind is very strong - decrease air pollution here
            self.air_pollution = self.decrease_by_percentage(self.air_pollution, 30/100)

        #change my temperature according to air pollution
        if random.choice([0,1]) == 1:
            self.temperature += 0.01*self.daily_temperature_increase()
        else:
            self.temperature -= 0.01*self.daily_temperature_increase()

        #calculate affect of wind on air pollution of neighbors
        affected_neighbor = self.get_neighbor(self.wind_direction, self.x, self.y, map_matrix)
        affected_neighbor.air_pollution = self.increase_by_percentage(affected_neighbor.air_pollution, self.wind_force/100)

        #if I am sea - generate rain
        if self.element == "water" and self.cloud != "rain cloud":
            chance = random.uniform(0,1)
            if chance <= 0.7:
                self.cloud = "rain cloud"

        #calculate if it will rain
        if self.cloud == "rain cloud":
            chance_of_rain = self.calculate_rain_chance(self.x, self.y, map_matrix, self.temperature, self.wind_force) #number between 1 and 100
            random_number = random.randint(1,100)
            if random_number <= chance_of_rain:
                #it will rain
                self.raining = True
                self.cloud = "cloudless" #tomorrow - no clouds
            else:
                #it will not rain
                self.raining = False
                self.cloud = "cloud" #change cloud status
                affected_neighbor.cloud = "rain cloud" #give rainy cloud to neighbor

        #decrease  my wind force
        self.wind_force = self.decrease_by_percentage(self.wind_force, 20/100)
        if self.element == "city":
            #less wind in cities
            self.wind_force = self.decrease_by_percentage(self.wind_force, 20/100)
        if self.element == "earth":
            #more wind in open areas
            self.wind_force = self.increase_by_percentage(self.wind_force, 15/100)

        #change wind direction
        if random.choice([0,1]) == 1: #rotate wind direction 45 degrees right
            if self.wind_direction == "N":
                self.wind_direction = "E"
            elif self.wind_direction == "E":
                self.wind_direction = "S"
            elif self.wind_direction == "S":
                self.wind_direction = "W"
            elif self.wind_direction == "W":
                self.wind_direction = "N"

        #increase my neighbors wind force
        affected_neighbor.wind_force = self.increase_by_percentage(affected_neighbor.wind_force, 20/100)

        #ice becomes water in global warming
        if self.temperature >= 40 and self.element == "ice":
            self.element = "water"

        if self.air_pollution < 0:
            self.air_pollution = 0

    def daily_temperature_increase(self):
        #used to calculate the value of the temperature increase
        #formula: temperature increase = a * air pollution + b* global warming state
        a = 0.1
        b = 0.2
        global_warming_state = random.uniform(GLOBAL_WARMING_STATE_A,GLOBAL_WARMING_STATE_B)
        return a*self.air_pollution + b*global_warming_state

    def get_air_pollution(self):
        # Assume current pollution levels
        # current_no2_level = 2
        # current_so2_level = 1
        # current_o3_level = 3

        #good simulation:
        current_no2_level = 0.01
        current_so2_level = 0.01
        current_o3_level = 0.01

        return (current_no2_level+ current_so2_level+ current_o3_level)//3
    def calculate_rain_chance(self, x, y, map_matrix, temperature, wind_force):

        dim = len(map_matrix)

        #higher chances of rain in norther and souther regions

        if y >= dim//2 and y <= dim//2 + 1:
            chance_of_rain = 10
        else:
            chance_of_rain = 40

        if temperature >= 10 and self.temperature <= 20:
            chance_of_rain += 20

        if temperature >=40 :
            chance_of_rain -=20 #too hot

        if wind_force >= 70:
            chance_of_rain += 20

        if self.element == "forest":
            if random.randint(0,1) == 1: #forest is rainforest - higher chance of rain
                chance_of_rain += 70

        return chance_of_rain

    def get_neighbor(self, wind_direction, x, y, map_matrix):
        neighbor_x = x
        neighbor_y = y
        dim = len(map_matrix)

        if wind_direction == "N":
            neighbor_y -= 1
        elif wind_direction == "S":
            neighbor_y += 1
        elif wind_direction == "E":
            neighbor_x += 1
        elif wind_direction == "W":
            neighbor_x -= 1

        if neighbor_x < 0:
            neighbor_x = dim - 1
        if neighbor_y < 0:
            neighbor_y = dim - 1
        if neighbor_x == dim:
            neighbor_x = 0
        if neighbor_y == dim:
            neighbor_y = 0

        return map_matrix[neighbor_x][neighbor_y]


    def increase_by_percentage(self, original_value, percentage_increase):
        # Check if the original value is negative
        is_negative = original_value < 0

        # Take the absolute value for the calculation
        absolute_value = abs(original_value)

        # Calculate the increase amount
        increase_amount = (absolute_value * percentage_increase) / 100

        # Calculate the new value
        if is_negative:
            new_value = absolute_value - increase_amount
        else:
            new_value = absolute_value + increase_amount


        # Restore the original sign
        new_value *= -1 if is_negative else 1

        return new_value
    def decrease_by_percentage(self, original_value, percentage_decrease):
        is_negative = original_value < 0
        decrease_amount = (abs(original_value) * percentage_decrease) / 100
        if is_negative:
            new_value = original_value + decrease_amount
        else:
            new_value = original_value - decrease_amount

        # if new_value < 0:
        #     new_value = 0
        return new_value

class World:
    def __init__(self):
        self.root = None
        self.matrix_size = 5
        self.create_World()
        self.update_paused = False
        self.day = 1



    def create_World(self):
        self.matrix = [
            [
                Cell(x=row, y=column)
                for column in range(self.matrix_size)
            ]
            for row in range(self.matrix_size)
        ]

        #first and last row must be ice:
        for i in range(0,len(self.matrix)):
            if i == 0 or i == len(self.matrix) - 1:
                for cell in self.matrix[i]:
                    cell.update_element("ice")



    def apply_rules(self):
        #iterate over all cells in matrix and run their apply_rules function
        #also calculate statistics

        cell_temperatures = []
        cell_air_pollution = []
        for row in self.matrix:
            for cell in row:
                cell.apply_rules(self.matrix)

                #save temperature average data
                cell_temperatures.append(cell.temperature)
                #save air pollution average
                cell_air_pollution.append(cell.air_pollution)

        self.create_statistics(cell_temperatures, cell_air_pollution)
        # self.standardize_data(4.692498966, self.day, r"C:\Users\Sandra study\PycharmProjects\pythonProject\temperature_data.csv")
        self.day += 1
        if self.day > 365:
            exit(0)
        print("day: ", self.day)

    def standardize_data(self, average_yearly_temp, day, stand_deviation_file):
        #for every day add a new row - with the standardized data value for each cell

        file_path = "standardized_data.csv"

        #if file is empty add headers
        if os.stat(file_path).st_size == 0:
            with open(file_path, 'a', newline='') as file:
                writer = csv.writer(file)
                first_row = ['Day']
                for row in self.matrix:
                    for cell in row:
                        first_row.append(f"Cell Row-{cell.x}, Cell Col - {cell.y}")
                writer.writerow(first_row)

        #calculate standardization values for all the cells in this day
        new_row = [day]
        for row in self.matrix:
            for cell in row:
                standard_deviation = self.get_standard_deviation_value(stand_deviation_file, day)
                assert standard_deviation is not None, "ERROR: Couldn't get standardized deviation value for day " + day
                standardized_value = (cell.temperature - average_yearly_temp ) / standard_deviation
                new_row.append(str(standardized_value))

        #write the values for this day
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(new_row)

    def get_standard_deviation_value(self, stand_deviation_file, day_id):
        assert os.path.exists(stand_deviation_file), "ERROR: This path doesn't exist - " + stand_deviation_file
        with open(stand_deviation_file, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            next(reader)  # Skip the header row if it exists

            for row in reader:
                row = row[0].split(",")
                if int(row[0]) == day_id:  # Assuming Day_ID is in the first column (index 0)
                    return float(row[3])  # Assuming Temperature Standard Deviation is in the fourth column (index 3)

        return None

    def create_statistics(self, temperatures, air_pollutions):
        mean_temperatures = np.mean(temperatures)
        mean_airps = np.mean(air_pollutions)

        # Calculate the squared differences
        squared_diff = (temperatures - mean_temperatures) ** 2

        # Calculate the variance
        variance = np.mean(squared_diff)

        # Calculate the standard deviation
        std_deviation = np.sqrt(variance)

        self.plot_average(mean_temperatures, mean_airps, std_deviation)
    def plot_average(self, temperature_average, air_pollution_average, temp_std_deviation):
        file_path = 'temperature_data.csv'  # Change the file path as needed

        # Check if the file already exists
        if not os.path.exists(file_path):
            # If the file doesn't exist, create it and write the header
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Day_ID', 'Temperature Average', 'Air Pollution Average', 'Temperature Standard Deviation', 'Global Warming State A', 'Global Warming State B', "Air Pollution Increase Factor"])

        # Append the data to the CSV file
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.day, temperature_average, air_pollution_average, temp_std_deviation, GLOBAL_WARMING_STATE_A, GLOBAL_WARMING_STATE_B, AIR_POLLUTION_AVERAGE])

    #GUI functions
    def build_GUI(self, image_size=(50, 50)):
        self.root = tk.Tk()
        self.root.title("Landscape Display")

        for i, row in enumerate(self.matrix):
            for j, cell in enumerate(row):
                element = cell.element
                if os.path.exists(f"{element}.png"):
                    image_path = f"{element}.png"  # Assuming image files are named after the elements
                    image = Image.open(image_path)
                    image = image.resize(image_size, PIL.Image.Resampling.LANCZOS)  # Resize the image to the specified size
                    image = ImageTk.PhotoImage(image)

                    label = tk.Label(self.root, image=image, relief=tk.RIDGE)
                    label.image = image  # Keep a reference to the image to prevent it from being garbage collected
                    label.grid(row=i*2, column=j)
                    # Adding labels with information
                    label_info = f"Temp: {cell.temperature}\nWind: {cell.wind_force} {self.display_wind_direction(cell.wind_direction)}\nRain: {cell.raining}\nAir: {cell.air_pollution}"

                    # Create a StringVar to update the label text
                    var = tk.StringVar()
                    var.set(label_info)
                    info_label = tk.Label(self.root, textvariable=var)
                    info_label.grid(row=i * 2 + 1, column=j)
                    info_label.info_var = var  # Add info_var attribute to the main label
                else:
                    print(f"ERROR: file {element}.png missing")

        self.stop_button = tk.Button(self.root, text="Pause/Resume", command=self.toggle_pause)
        self.stop_button.grid(row=0, column=j+1, rowspan=len(self.matrix),
                              sticky="ns")  # Use sticky="ns" to make it fill vertically

        self.root.after(UPDATE_TIME, self.redraw)
        self.root.mainloop()

    def toggle_pause(self):
        self.update_paused = not self.update_paused
        print("changed update_paused to ", self.update_paused)

    def redraw(self):
        if not self.update_paused:
            self.apply_rules()
            self.edit_GUI()
            # Reschedule the edit_GUI function to run again after UPDATE_TIME
            self.root.after(UPDATE_TIME, self.redraw)
        else:
            # If updates are paused, reschedule the function to check again after 500 milliseconds
            self.root.after(500, self.redraw)

    def edit_GUI(self):
        for row in self.matrix:
            for cell in row:
                new_text = f"Temp: {cell.temperature}\nWind: {cell.wind_force} {self.display_wind_direction(cell.wind_direction)}\nRain: {cell.raining}\nAir: {cell.air_pollution}"
                self.update_label(cell.x, cell.y, new_text)

                # Check if the element has changed, and update the image accordingly
                self.update_cell_image(cell.x * 2, cell.y, cell.element)

    def update_label(self, row, column, new_text):
        # Find the label in the specified row and column
        row = row*2+1
        label = self.root.grid_slaves(row=row, column=column)[0]  # Assuming there's only one label in the specified location

        # Update the text content of the label
        label.info_var.set(new_text)

    def update_cell_image(self, row, column, new_element):
        image_path = f"{new_element}.png"
        new_image = Image.open(image_path)
        new_image = new_image.resize((50, 50), PIL.Image.Resampling.LANCZOS)
        new_image = ImageTk.PhotoImage(new_image)

        label = self.root.grid_slaves(row=row, column=column)[0]
        label.config(image=new_image)
        label.image = new_image
        label.element = new_element

    def display_wind_direction(self, wind_direction):
        if wind_direction == "N":
            return "↑"
        elif wind_direction == "S":
            return "↓"
        elif wind_direction == "E":
            return "→"
        elif wind_direction == "W":
            return "←"

    def reduce_cities(self, new_city_count):
        count = 0
        for row in self.matrix:
            for cell in row:
                if cell.element == "city":
                    count += 1

        if count > new_city_count:
            for row in self.matrix:
                for cell in row:
                    if cell.element == "city" and count > new_city_count:
                        cell.update_element(random.choice(["earth", "water", "forest"]))
                        count -= 1





world = World()
world.reduce_cities(new_city_count=1) #for last question

#############run the gUI:##################
# world.build_GUI()
###########################################

#############run only the rule changes (for statistics): #################
while True:
    world.apply_rules()

##########################################################################


