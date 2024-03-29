import numpy
import functools
from scipy.special import expit
import pickle

# Supported activation functions by the cnn.py module.
supported_activation_functions = ("sigmoid", "relu", "softmax")

def sigmoid(sop):
    if type(sop) in [list, tuple]:
        sop = numpy.array(sop)
    return 1.0 / (1 + numpy.exp(-1 * sop))

# def relu(sop):
#     if not (type(sop) in [list, tuple, numpy.ndarray]):
#         if sop < 0:
#             return 0
#         else:
#             return sop
#     elif type(sop) in [list, tuple]:
#         sop = numpy.array(sop)

#     result = sop
#     result[sop < 0] = 0
#     return result

def relu(sop):
    if isinstance(sop, (int, float)):
        return max(0, sop)
    elif isinstance(sop, (list, tuple, numpy.ndarray)):
        return numpy.maximum(0, sop)
    else:
        raise ValueError("Unsupported input type for relu activation.")


def relu_derivative(x):
    return 1.0 * (x > 0)

def softmax(layer_outputs):
    return layer_outputs / (numpy.sum(layer_outputs) + 0.000001)

def layers_weights(model, initial=True):
    network_weights = []
    layer = model.last_layer
    while "previous_layer" in layer.__init__.__code__.co_varnames:
        if type(layer) in [Conv2D, Dense]:
            # If the 'initial' parameter is True, append the initial weights. Otherwise, append the trained weights.
            if initial == True:
                network_weights.append(layer.initial_weights)
            elif initial == False:
                network_weights.append(layer.trained_weights)
            else:
                raise ValueError("Unexpected value to the 'initial' parameter: {initial}.".format(initial=initial))

        # Go to the previous layer.
        layer = layer.previous_layer

    # If the first layer in the network is not an input layer (i.e. an instance of the Input2D class), raise an error.
    if not (type(layer) is Input2D):
        raise TypeError("The first layer in the network architecture must be an input layer.")
    network_weights.reverse()
    return numpy.array(network_weights)

def layers_weights_as_matrix(model, vector_weights):
    network_weights = []

    start = 0
    layer = model.last_layer
    vector_weights = vector_weights[::-1]
    while "previous_layer" in layer.__init__.__code__.co_varnames:
        if type(layer) in [Conv2D, Dense]:
            layer_weights_shape = layer.initial_weights.shape
            layer_weights_size = layer.initial_weights.size
    
            weights_vector=vector_weights[start:start + layer_weights_size]
    #        matrix = pygad.nn.DenseLayer.to_array(vector=weights_vector, shape=layer_weights_shape)
            matrix = numpy.reshape(weights_vector, newshape=(layer_weights_shape))
            network_weights.append(matrix)
    
            start = start + layer_weights_size
    
        # Go to the previous layer.
        layer = layer.previous_layer

    # If the first layer in the network is not an input layer (i.e. an instance of the Input2D class), raise an error.
    if not (type(layer) is Input2D):
        raise TypeError("The first layer in the network architecture must be an input layer.")

    # Currently, the weights of the layers are in the reverse order. In other words, the weights of the first layer are at the last index of the 'network_weights' list while the weights of the last layer are at the first index.
    # Reversing the 'network_weights' list to order the layers' weights according to their location in the network architecture (i.e. the weights of the first layer appears at index 0 of the list).
    network_weights.reverse()
    return numpy.array(network_weights)

def layers_weights_as_vector(model, initial=True):
    network_weights = []

    layer = model.last_layer
    while "previous_layer" in layer.__init__.__code__.co_varnames:
        if type(layer) in [Conv2D, Dense]:
            # If the 'initial' parameter is True, append the initial weights. Otherwise, append the trained weights.
            if initial == True:
                vector = numpy.reshape(layer.initial_weights, newshape=(layer.initial_weights.size))
    #            vector = pygad.nn.DenseLayer.to_vector(matrix=layer.initial_weights)
                network_weights.extend(vector)
            elif initial == False:
                vector = numpy.reshape(layer.trained_weights, newshape=(layer.trained_weights.size))
    #            vector = pygad.nn.DenseLayer.to_vector(array=layer.trained_weights)
                network_weights.extend(vector)
            else:
                raise ValueError("Unexpected value to the 'initial' parameter: {initial}.".format(initial=initial))

        # Go to the previous layer.
        layer = layer.previous_layer

    # If the first layer in the network is not an input layer (i.e. an instance of the Input2D class), raise an error.
    if not (type(layer) is Input2D):
        raise TypeError("The first layer in the network architecture must be an input layer.")

    # Currently, the weights of the layers are in the reverse order. In other words, the weights of the first layer are at the last index of the 'network_weights' list while the weights of the last layer are at the first index.
    # Reversing the 'network_weights' list to order the layers' weights according to their location in the network architecture (i.e. the weights of the first layer appears at index 0 of the list).
    network_weights.reverse()
    return numpy.array(network_weights)

def update_layers_trained_weights(model, final_weights):
    layer = model.last_layer
    layer_idx = len(final_weights) - 1
    while "previous_layer" in layer.__init__.__code__.co_varnames:
        if type(layer) in [Conv2D, Dense]:
            layer.trained_weights = final_weights[layer_idx]   
            layer_idx = layer_idx - 1

        # Go to the previous layer.
        layer = layer.previous_layer

class Input2D:
    def __init__(self, input_shape):
        # If the input sample has less than 2 dimensions, then an exception is raised.
        if len(input_shape) < 2:
            raise ValueError("The Input2D class creates an input layer for data inputs with at least 2 dimensions but ({num_dim}) dimensions found.".format(num_dim=len(input_shape)))
        # If the input sample has exactly 2 dimensions, the third dimension is set to 1.
        elif len(input_shape) == 2:
            input_shape = (input_shape[0], input_shape[1], 1)

        for dim_idx, dim in enumerate(input_shape):
            if dim <= 0:
                raise ValueError("The dimension size of the inputs cannot be <= 0. Please pass a valid value to the 'input_size' parameter.")

        self.input_shape = input_shape # Shape of the input sample.
        self.layer_output_size = input_shape # Shape of the output from the current layer. For an input layer, it is the same as the shape of the input sample.

class Conv2D:
    def __init__(self, num_filters, kernel_size, previous_layer, activation_function=None):
        if num_filters <= 0:
            raise ValueError("Number of filters cannot be <= 0. Please pass a valid value to the 'num_filters' parameter.")
        # Number of filters in the conv layer.
        self.num_filters = num_filters

        if kernel_size <= 0:
            raise ValueError("The kernel size cannot be <= 0. Please pass a valid value to the 'kernel_size' parameter.")
        # Kernel size of each filter.
        self.kernel_size = kernel_size

        # Validating the activation function
        if (activation_function is None):
            self.activation = None
        elif (activation_function == "relu"):
            self.activation = relu
        elif (activation_function == "sigmoid"):
            self.activation = sigmoid
        elif (activation_function == "softmax"):
            raise ValueError("The softmax activation function cannot be used in a conv layer.")
        else:
            raise ValueError("The specified activation function '{activation_function}' is not among the supported activation functions {supported_activation_functions}. Please use one of the supported functions.".format(activation_function=activation_function, supported_activation_functions=supported_activation_functions))

        # The activation function used in the current layer.
        self.activation_function = activation_function

        if previous_layer is None:
            raise TypeError("The previous layer cannot be of Type 'None'. Please pass a valid layer to the 'previous_layer' parameter.")
        # A reference to the layer that preceeds the current layer in the network architecture.
        self.previous_layer = previous_layer
        
        # A reference to the bank of filters.
        self.filter_bank_size = (self.num_filters,
                                 self.kernel_size, 
                                 self.kernel_size, 
                                 self.previous_layer.layer_output_size[-1])

        # Initializing the filters of the conv layer.
        self.initial_weights = numpy.random.uniform(low=-0.1,
                                                    high=0.1,
                                                    size=self.filter_bank_size)

        # The trained filters of the conv layer. Only assigned a value after the network is trained (i.e. the train_network() function completes).
        # Just initialized to be equal to the initial filters
        self.trained_weights = self.initial_weights.copy()

        # Size of the input to the layer.
        self.layer_input_size = self.previous_layer.layer_output_size

        # Size of the output from the layer.
        # Later, it must conider strides and paddings
        self.layer_output_size = (self.previous_layer.layer_output_size[0] - self.kernel_size + 1, 
                                  self.previous_layer.layer_output_size[1] - self.kernel_size + 1, 
                                  num_filters)

        # The layer_output attribute holds the latest output from the layer.
        self.layer_output = None

    def conv_(self, input2D, conv_filter):

        result = numpy.zeros(shape=(input2D.shape[0], input2D.shape[1], conv_filter.shape[0]))
        # Looping through the image to apply the convolution operation.
        for r in numpy.uint16(numpy.arange(self.filter_bank_size[1]/2.0, 
                              input2D.shape[0]-self.filter_bank_size[1]/2.0+1)):
            for c in numpy.uint16(numpy.arange(self.filter_bank_size[1]/2.0, 
                                               input2D.shape[1]-self.filter_bank_size[1]/2.0+1)):

                if len(input2D.shape) == 2:
                    curr_region = input2D[r-numpy.uint16(numpy.floor(self.filter_bank_size[1]/2.0)):r+numpy.uint16(numpy.ceil(self.filter_bank_size[1]/2.0)), 
                                          c-numpy.uint16(numpy.floor(self.filter_bank_size[1]/2.0)):c+numpy.uint16(numpy.ceil(self.filter_bank_size[1]/2.0))]
                else:
                    curr_region = input2D[r-numpy.uint16(numpy.floor(self.filter_bank_size[1]/2.0)):r+numpy.uint16(numpy.ceil(self.filter_bank_size[1]/2.0)), 
                                          c-numpy.uint16(numpy.floor(self.filter_bank_size[1]/2.0)):c+numpy.uint16(numpy.ceil(self.filter_bank_size[1]/2.0)), :]
                # Element-wise multipliplication between the current region and the filter.
                
                for filter_idx in range(conv_filter.shape[0]):
                    curr_result = curr_region * conv_filter[filter_idx]
                    conv_sum = numpy.sum(curr_result) # Summing the result of multiplication.
    
                    if self.activation is None:
                        result[r, c, filter_idx] = conv_sum # Saving the SOP in the convolution layer feature map.
                    else:
                        result[r, c, filter_idx] = self.activation(conv_sum) # Saving the activation function result in the convolution layer feature map.

        # Clipping the outliers of the result matrix.
        final_result = result[numpy.uint16(self.filter_bank_size[1]/2.0):result.shape[0]-numpy.uint16(self.filter_bank_size[1]/2.0), 
                              numpy.uint16(self.filter_bank_size[1]/2.0):result.shape[1]-numpy.uint16(self.filter_bank_size[1]/2.0), :]
        return final_result

    def conv(self, input2D):
        if len(input2D.shape) != len(self.initial_weights.shape) - 1: # Check if there is a match in the number of dimensions between the image and the filters.
            raise ValueError("Number of dimensions in the conv filter and the input do not match.")  
        if len(input2D.shape) > 2 or len(self.initial_weights.shape) > 3: # Check if number of image channels matches the filter depth.
            if input2D.shape[-1] != self.initial_weights.shape[-1]:
                raise ValueError("Number of channels in both the input and the filter must match.")
        if self.initial_weights.shape[1] != self.initial_weights.shape[2]: # Check if filter dimensions are equal.
            raise ValueError('A filter must be a square matrix. I.e. number of rows and columns must match.')
        if self.initial_weights.shape[1]%2==0: # Check if filter diemnsions are odd.
            raise ValueError('A filter must have an odd size. I.e. number of rows and columns must be odd.')

        self.layer_output = self.conv_(input2D, self.trained_weights)

class AveragePooling2D:
    def __init__(self, pool_size, previous_layer, stride=2):
        if not (type(pool_size) is int):
            raise ValueError("The expected type of the pool_size is int but {pool_size_type} found.".format(pool_size_type=type(pool_size)))

        if pool_size <= 0:
            raise ValueError("The passed value to the pool_size parameter cannot be <= 0.")
        self.pool_size = pool_size

        if stride <= 0:
            raise ValueError("The passed value to the stride parameter cannot be <= 0.")
        self.stride = stride

        if previous_layer is None:
            raise TypeError("The previous layer cannot be of Type 'None'. Please pass a valid layer to the 'previous_layer' parameter.")
        # A reference to the layer that preceeds the current layer in the network architecture.
        self.previous_layer = previous_layer

        # Size of the input to the layer.
        self.layer_input_size = self.previous_layer.layer_output_size

        # Size of the output from the layer.
        self.layer_output_size = (numpy.uint16((self.previous_layer.layer_output_size[0] - self.pool_size + 1)/stride + 1), 
                                  numpy.uint16((self.previous_layer.layer_output_size[1] - self.pool_size + 1)/stride + 1), 
                                  self.previous_layer.layer_output_size[-1])

        # The layer_output attribute holds the latest output from the layer.
        self.layer_output = None

    def average_pooling(self, input2D):
        # Preparing the output of the pooling operation.
        pool_out = numpy.zeros((numpy.uint16((input2D.shape[0]-self.pool_size+1)/self.stride+1),
                                numpy.uint16((input2D.shape[1]-self.pool_size+1)/self.stride+1),
                                input2D.shape[-1]))
        for map_num in range(input2D.shape[-1]):
            r2 = 0
            for r in numpy.arange(0,input2D.shape[0]-self.pool_size+1, self.stride):
                c2 = 0
                for c in numpy.arange(0, input2D.shape[1]-self.pool_size+1, self.stride):
                    pool_out[r2, c2, map_num] = numpy.mean([input2D[r:r+self.pool_size,  c:c+self.pool_size, map_num]])
                    c2 = c2 + 1
                r2 = r2 +1

        self.layer_output = pool_out

class MaxPooling2D:
    def __init__(self, pool_size, previous_layer, stride=2):     
        if not (type(pool_size) is int):
            raise ValueError("The expected type of the pool_size is int but {pool_size_type} found.".format(pool_size_type=type(pool_size)))

        if pool_size <= 0:
            raise ValueError("The passed value to the pool_size parameter cannot be <= 0.")
        self.pool_size = pool_size

        if stride <= 0:
            raise ValueError("The passed value to the stride parameter cannot be <= 0.")
        self.stride = stride

        if previous_layer is None:
            raise TypeError("The previous layer cannot be of Type 'None'. Please pass a valid layer to the 'previous_layer' parameter.")
        # A reference to the layer that preceeds the current layer in the network architecture.
        self.previous_layer = previous_layer

        # Size of the input to the layer.
        self.layer_input_size = self.previous_layer.layer_output_size

        # Size of the output from the layer.
        self.layer_output_size = (numpy.uint16((self.previous_layer.layer_output_size[0] - self.pool_size + 1)/stride + 1), 
                                  numpy.uint16((self.previous_layer.layer_output_size[1] - self.pool_size + 1)/stride + 1), 
                                  self.previous_layer.layer_output_size[-1])

        # The layer_output attribute holds the latest output from the layer.
        self.layer_output = None

    def max_pooling(self, input2D):
        # Preparing the output of the pooling operation.
        pool_out = numpy.zeros((numpy.uint16((input2D.shape[0]-self.pool_size+1)/self.stride+1),
                                numpy.uint16((input2D.shape[1]-self.pool_size+1)/self.stride+1),
                                input2D.shape[-1]))
        for map_num in range(input2D.shape[-1]):
            r2 = 0
            for r in numpy.arange(0,input2D.shape[0]-self.pool_size+1, self.stride):
                c2 = 0
                for c in numpy.arange(0, input2D.shape[1]-self.pool_size+1, self.stride):
                    pool_out[r2, c2, map_num] = numpy.max([input2D[r:r+self.pool_size,  c:c+self.pool_size, map_num]])
                    c2 = c2 + 1
                r2 = r2 +1

        self.layer_output = pool_out

class ReLU:

    def __init__(self, previous_layer):

        if previous_layer is None:
            raise TypeError("The previous layer cannot be of Type 'None'. Please pass a valid layer to the 'previous_layer' parameter.")

        # A reference to the layer that preceeds the current layer in the network architecture.
        self.previous_layer = previous_layer

        # Size of the input to the layer.
        self.layer_input_size = self.previous_layer.layer_output_size

        # Size of the output from the layer.
        self.layer_output_size = self.previous_layer.layer_output_size

        # The layer_output attribute holds the latest output from the layer.
        self.layer_output = None

    # def relu_layer(self, layer_input):

    #     self.layer_output_size = layer_input.size
    #     self.layer_output = relu(layer_input)

    def relu_layer(self, layer_input):
        self.layer_output_size = layer_input.size
        self.layer_output = relu(layer_input)

    def relu_derivative_layer(self, layer_input):
        return relu_derivative(layer_input)

class Sigmoid:
    def __init__(self, previous_layer):
        if previous_layer is None:
            raise TypeError("The previous layer cannot be of Type 'None'. Please pass a valid layer to the 'previous_layer' parameter.")
        # A reference to the layer that preceeds the current layer in the network architecture.
        self.previous_layer = previous_layer

        # Size of the input to the layer.
        self.layer_input_size = self.previous_layer.layer_output_size

        # Size of the output from the layer.
        self.layer_output_size = self.previous_layer.layer_output_size

        # The layer_output attribute holds the latest output from the layer.
        self.layer_output = None

    def sigmoid_layer(self, layer_input):
        self.layer_output_size = layer_input.size
        self.layer_output = sigmoid(layer_input)

class Flatten:

    def __init__(self, previous_layer):

        if previous_layer is None:
            raise TypeError("The previous layer cannot be of Type 'None'. Please pass a valid layer to the 'previous_layer' parameter.")
        # A reference to the layer that preceeds the current layer in the network architecture.
        self.previous_layer = previous_layer

        # Size of the input to the layer.
        self.layer_input_size = self.previous_layer.layer_output_size

        # Size of the output from the layer.
        self.layer_output_size = functools.reduce(lambda x, y: x*y, self.previous_layer.layer_output_size)

        # The layer_output attribute holds the latest output from the layer.
        self.layer_output = None

    def flatten(self, input2D):

        self.layer_output_size = input2D.size
        self.layer_output = numpy.ravel(input2D)

    def compute_gradients(self, loss):
        # Reshape the loss to match the original shape before flattening
        return loss.reshape(self.previous_layer.layer_output.shape)

    def set_next_layer(self, next_layer):
        self.next_layer = next_layer

class Dense:
    def __init__(self, num_neurons, previous_layer, activation_function="relu"):

        if num_neurons <= 0:
            raise ValueError("Number of neurons cannot be <= 0. Please pass a valid value to the 'num_neurons' parameter.")

        # Number of neurons in the dense layer.
        self.num_neurons = num_neurons

        # Validating the activation function
        if (activation_function == "relu"):
            self.activation = relu
            self.activation_derivative = relu_derivative
        elif (activation_function == "sigmoid"):
            self.activation = sigmoid
        elif (activation_function == "softmax"):
            self.activation = softmax
        else:
            raise ValueError("The specified activation function '{activation_function}' is not among the supported activation functions {supported_activation_functions}. Please use one of the supported functions.".format(activation_function=activation_function, supported_activation_functions=supported_activation_functions))

        self.activation_function = activation_function

        if previous_layer is None:
            raise TypeError("The previous layer cannot be of Type 'None'. Please pass a valid layer to the 'previous_layer' parameter.")
        # A reference to the layer that preceeds the current layer in the network architecture.
        self.previous_layer = previous_layer
        
        if type(self.previous_layer.layer_output_size) in [list, tuple, numpy.ndarray] and len(self.previous_layer.layer_output_size) > 1:
            raise ValueError("The input to the dense layer must be of type int but {sh} found.".format(sh=type(self.previous_layer.layer_output_size)))
        # Initializing the weights of the layer.
        self.initial_weights = numpy.random.uniform(low=-0.1,
                                                    high=0.1,
                                                    size=(self.previous_layer.layer_output_size, self.num_neurons))

        # The trained weights of the layer. Only assigned a value after the network is trained (i.e. the train_network() function completes).
        # Just initialized to be equal to the initial weights
        self.trained_weights = self.initial_weights.copy()

        # Size of the input to the layer.
        self.layer_input_size = self.previous_layer.layer_output_size

        # Size of the output from the layer.
        self.layer_output_size = num_neurons

        # The layer_output attribute holds the latest output from the layer.
        self.layer_output = None

    # def dense_layer(self, layer_input):

    #     if self.trained_weights is None:
    #         raise TypeError("The weights of the dense layer cannot be of Type 'None'.")

    #     sop = numpy.matmul(layer_input, self.trained_weights)

    #     self.layer_output = self.activation(sop)


    def dense_layer(self, layer_input):
        if self.trained_weights is None:
            raise TypeError("The weights of the dense layer cannot be of Type 'None'.")

        sop = numpy.matmul(layer_input, self.trained_weights)
        self.layer_output = self.activation(sop)

    def relu_derivative(self, x):
        return numpy.where(x <= 0, 0, 1)

    def set_next_layer(self, next_layer):
        self.next_layer = next_layer

    def softmax_derivative(self, x):
        # Assuming you have already implemented the softmax function
        softmax_values = softmax(x)
        return softmax_values * (1 - softmax_values)

    def activation_derivative(self, x):
        if self.activation_function == "relu":
            return self.relu_derivative(x)
        elif self.activation_function == "sigmoid":
            return sigmoid_derivative(x)
        elif self.activation_function == "softmax":
            return self.softmax_derivative(x)
        else:
            raise ValueError("Unsupported activation function: {}".format(self.activation_function))


    def compute_gradients(self, loss):
        # Create a dictionary to store gradients for each layer's weights
        gradients = {}

        # Backpropagation starts here (assuming a feedforward network)
        # Compute gradients for the output layer
        gradients_output_layer = self.activation_derivative(self.layer_output) * loss
        gradients[self] = gradients_output_layer

        # Perform backpropagation through the layers to compute gradients for each layer's weights
        layer = self
        while layer.previous_layer:
            gradients[layer.previous_layer] = layer.previous_layer.compute_gradients(numpy.matmul(gradients[layer], layer.trained_weights.T))
            layer = layer.previous_layer

        return gradients

    def update_weights(self, gradients):
        # Adjust weights using the gradients
        if "trained_weights" in vars(self):
            self.trained_weights -= self.learning_rate * np.matmul(self.previous_layer.layer_output.T, gradients[self])


class Model:

    def get_layers(self):
        network_layers = []

        # The last layer in the network archietcture.
        layer = self.last_layer

        while "previous_layer" in layer.__init__.__code__.co_varnames:
            network_layers.insert(0, layer)
            layer = layer.previous_layer

        return network_layers

    def __init__(self, last_layer, epochs=10, learning_rate=0.01, batch_size=32):
        self.last_layer = last_layer
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.network_layers = self.get_layers()


# Inside the Model class
    def compute_loss(self, predicted, target):
        epsilon = 1e-10  # Small value to prevent log(0)
    
        # Convert the predicted and target values to numpy arrays if they're not already
        predicted = numpy.array(predicted)
        target = numpy.array(target)
    
        # Compute the loss using categorical cross-entropy
        loss = -numpy.sum(target * numpy.log(predicted + epsilon))
    
        return loss

    
    def compute_gradients(self, loss):
        # Create a dictionary to store gradients for each layer's weights
        gradients = {}

        # Backpropagation starts here (assuming a feedforward network)
        # Compute gradients for the output layer
        output_layer = self.last_layer  # Get the output layer of the model
        gradients_output_layer = output_layer.compute_gradients(loss)

        # Store gradients for the output layer
        gradients[output_layer] = gradients_output_layer

        # Perform backpropagation through the layers to compute gradients for each layer's weights
        for layer in reversed(self.network_layers[1:]):  # Start from the last hidden layer
            gradients[layer] = layer.compute_gradients(gradients[layer.next_layer])

        # Update weights using the gradients
        for layer in self.network_layers:
            layer.update_weights(gradients[layer])

        return gradients


    def train(self, train_inputs, train_outputs):
    # Check input dimensions and compatibility
        if train_inputs.ndim != 4:
            raise ValueError("Training data input must have 4 dimensions: (num_samples, width, height, channels)")
        if train_inputs.shape[0] != len(train_outputs):
            raise ValueError("Number of input samples must match the number of labels.")
        
        for epoch in range(self.epochs):
            print(f"Epoch {epoch + 1}/{self.epochs}")

            # Loop through the training data in mini-batches
            for sample_idx in range(0, len(train_inputs), self.batch_size):
                batch_inputs = train_inputs[sample_idx: sample_idx + self.batch_size]
                batch_outputs = train_outputs[sample_idx: sample_idx + self.batch_size]

                # Forward pass: compute predicted outputs
                predictions = self.predict(batch_inputs)

                # Compute loss (you need to define this method)
                loss = self.compute_loss(predictions, batch_outputs)

                # Backpropagation: compute gradients (you need to define this method)
                gradients = self.compute_gradients(loss)

                # Update weights (you need to define this method)
                self.update_weights(gradients)

                # Display training progress if needed
                training_percentage = (sample_idx + len(batch_inputs)) / len(train_inputs) * 100
                print(f"Training Percentage: {training_percentage:.2f}%")


    def feed_sample(self, sample):
        last_layer_outputs = sample
        for layer in self.network_layers:
            if type(layer) is Conv2D:
#                import time
#                time1 = time.time()
                layer.conv(input2D=last_layer_outputs)
#                time2 = time.time()
#                print(time2 - time1)
            elif type(layer) is Dense:
                layer.dense_layer(layer_input=last_layer_outputs)
            elif type(layer) is MaxPooling2D:
                layer.max_pooling(input2D=last_layer_outputs)
            elif type(layer) is AveragePooling2D:
                layer.average_pooling(input2D=last_layer_outputs)
            elif type(layer) is ReLU:
                layer.relu_layer(layer_input=last_layer_outputs)
            elif type(layer) is Sigmoid:
                layer.sigmoid_layer(layer_input=last_layer_outputs)
            elif type(layer) is Flatten:
                layer.flatten(input2D=last_layer_outputs)
            elif type(layer) is Input2D:
                pass
            else:
                print("Other")
                raise TypeError("The layer of type {layer_type} is not supported yet.".format(layer_type=type(layer)))

            last_layer_outputs = layer.layer_output
        return self.network_layers[-1].layer_output

    def update_weights(self, network_error):

        for layer in self.network_layers:
            if "trained_weights" in vars(layer).keys():
                layer.trained_weights = layer.trained_weights - network_error * self.learning_rate * layer.trained_weights


    def predict(self, data_inputs):

        if (data_inputs.ndim != 4):
            raise ValueError("The data input has {num_dims} but it must have 4 dimensions. The first dimension is the number of training samples, the second & third dimensions represent the width and height of the sample, and the fourth dimension represents the number of channels in the sample.".format(num_dims=data_inputs.ndim))

        predictions = []
        for sample in data_inputs:
            probs = self.feed_sample(sample=sample)
            predicted_label = numpy.where(numpy.max(probs) == probs)[0][0]
            predictions.append(predicted_label)
        return predictions

    def summary(self):

        """
        Prints a summary of the CNN architecture.
        """

        print("\n----------Network Architecture----------")
        for layer in self.network_layers:
            print(type(layer))
        print("----------------------------------------\n")
