import random
import time

from PIL import Image, ImageTk
import PIL
import os
import tkinter as tk

UPDATE_TIME =  2000 #1 second
INITIAL_POLLUTION_RANGE = list(range(40,60))
kjhk

#TODO check why temperature isn't changing in non-ice elements
#TODO change clouds and rain handling - rain is formed only from cloud cells, and will come from cloud cells

class Cell:
    def __init__(self, x, y ):
        self.x = x
        self.y = y
        self.element = random.choice(["earth", "water", "forest", "city"]) #ice element also exists, but cannot be randomly chosen
        if self.element == "city":
            self.air_pollution = random.choice(INITIAL_POLLUTION_RANGE)
        else:
            self.air_pollution = 10 #very little air pollution to start with if its not a city
        self.cloud = random.choice(["cloud", "rain cloud", "cloudless"]) #either 'cloud', 'rain cloud' or None
        self.wind_force = random.randint(1,100)
        self.wind_direction = random.choice(["N", "E", "W", "S"]) #from N, E, W, S
        self.temperature = self.define_temp()
        self.raining = False

        self.air_pollution_range = list(range(-5, 16)) #air pollution in cities can increase on a daily basis with percentages in this range

    def update_element(self, new_element):
        self.element = new_element
        self.temperature = self.define_temp()
    def define_temp(self):
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
            self.air_pollution = self.decrease_by_percentage(self.air_pollution, 5/100)
        elif self.element == "city": #increase air pollution in cities
            self.air_pollution = self.increase_by_percentage(self.air_pollution, random.choice(self.air_pollution_range)/100)
        if self.wind_force > 70: #if wind is very strong - decrease air pollution here
            self.air_pollution = self.decrease_by_percentage(self.air_pollution, 15/100)

        #change my temperature according to air pollution
        self.temperature = self.increase_by_percentage(self.temperature, self.air_pollution/100)

        #calculate affect of wind on air pollution of neighbors
        affected_neighbor = self.get_neighbor(self.wind_direction, self.x, self.y, map_matrix)
        affected_neighbor.air_pollution = self.increase_by_percentage(affected_neighbor.air_pollution, self.wind_force/100)

        #if I am sea - generate rain
        if self.element == "water" and self.cloud != "rain cloud":
            chance = random.choice([0,1])
            if chance == 1:
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


    def calculate_rain_chance(self, x, y, map_matrix, temperature, wind_force):
        chance_of_rain = 0

        dim = len(map_matrix)
        #higher chances of rain in norther and souther regions
        if y >= dim//2 and y <= dim//2 + 1:
            chance_of_rain = 10
        else:
            chance_of_rain = 40

        if temperature >= 10 and self.temperature <= 20:
            chance_of_rain += 20

        if wind_force >= 70:
            chance_of_rain += 20

        return chance_of_rain

    def get_neighbor(self, wind_direction, x, y, map_matrix):
        neighbor_x = x
        neighbor_y = y
        dim = len(map_matrix)

        if wind_direction == "N":
            neighbor_y -= 1
        elif wind_direction== "S":
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

        return int(new_value)
    def decrease_by_percentage(self, original_value, percentage_decrease):
        is_negative = original_value < 0
        decrease_amount = (abs(original_value) * percentage_decrease) / 100
        if is_negative:
            new_value = original_value + decrease_amount
        else:
            new_value = original_value - decrease_amount

        # if new_value < 0:
        #     new_value = 0
        return int(new_value)

class World:
    def __init__(self):
        self.root = None
        self.matrix_size = 5
        # self.landscape_matrix = self.create_landscape_matrix(image_size=(self.matrix_size, self.matrix_size))
        # self.temperature_matrix = self.create_temperature_matrix(dim = self.matrix_size)
        self.create_World()
        self.update_paused = False


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
    #using environment values in cell in this row and column - update environment values in all other cells
        for row in self.matrix:
            for cell in row:
                cell.apply_rules(self.matrix)


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



world = World()
world.build_GUI()

