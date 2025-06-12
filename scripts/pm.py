# Import libraries
import os
import numpy as np
import cv2
from scipy.signal import convolve2d

# exp(-(imgradient(img)./K).^2)
def g_0(img, K) -> np.ndarray:
    # Magnitude of gradients = sqrt(x_gradient^2 + y_gradient^2)
    s_x = cv2.Sobel(img, dx=1, dy=0, ddepth=cv2.CV_64F)
    s_y = cv2.Sobel(img, dx=0, dy=1, ddepth=cv2.CV_64F)
    return np.exp(-(np.hypot(s_x, s_y) / K)**2.0)

# 1 ./ (1 + (imgradient(x)./K).^2)
def g_1(img, K) -> np.ndarray:
    # Magnitude of gradients = sqrt(x_gradient^2 + y_gradient^2)
    s_x = cv2.Sobel(img, dx=1, dy=0, ddepth=cv2.CV_64F)
    s_y = cv2.Sobel(img, dx=0, dy=1, ddepth=cv2.CV_64F)
    return 1 / (1 + (np.hypot(s_x, s_y) / K)**2.0)

# Algorithm on one colour channel, to be run in parallel
def perona_malik(U, g, ts, K, w, h) -> np.ndarray:
    grad = g(U, K) # Take gradient
    grad[0, :] = np.zeros((1, w+2)); grad[h+1, :] = np.zeros((1, w+2)) # Apply Neumann boundary conditions
    grad[:, 0] = np.zeros((h+2)); grad[:, w+1] = np.zeros((h+2)) # Gradient on boundary = 0

    # Convolutions. Four for each cardinal direction. It's actually ridiculous how much better this is compared to a nested for loop
    north = convolve2d(U, np.array([[0, 1, 0], [0, -1, 0], [0, 0, 0]]), boundary="symm", mode="same") * convolve2d(grad, np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]]), boundary="symm", mode="same")
    south = convolve2d(U, np.array([[0, 0, 0], [0, -1, 0], [0, 1, 0]]), boundary="symm", mode="same") * convolve2d(grad, np.array([[0, 0, 0], [0, 0, 0], [0, 1, 0]]), boundary="symm", mode="same")
    east = convolve2d(U, np.array([[0, 0, 0], [0, -1, 1], [0, 0, 0]]), boundary="symm", mode="same") * convolve2d(grad, np.array([[0, 0, 0], [0, 0, 1], [0, 0, 0]]), boundary="symm", mode="same")
    west = convolve2d(U, np.array([[0, 0, 0], [1, -1, 0], [0, 0, 0]]), boundary="symm", mode="same") * convolve2d(grad, np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0]]), boundary="symm", mode="same")

    return U + ts * (north + south + east + west)

# Main body of the script
def main(image_channel, iterations, time_step_size, k, g_func, upload_path, result_path, image_name):
    img = cv2.imread(os.path.join(upload_path, image_name))[:, :, image_channel]
    # Rescale the pixel intensities from [0, 255] to [0, 1]
    img = img/255.0
    
    # Apply Dirchlet border conditions (place a border of 0 around image)
    w = img.shape[1]; h = img.shape[0] # Get image dimensions
    U = np.zeros((h+2, w+2))
    U[1:h+1, 1:w+1] = img
    
    # Store g function, either g_0 or g_1 depending on what was used in the command line argument
    if g_func:
        g = g_1
    else:
        g = g_0
    
    # Prepare for the loop
    N = iterations

    # Begin the loop
    for _ in range(N):
        # The Perona-Malik algorithm is called here
        U = perona_malik(U, g, time_step_size, k, w, h)

    # Rescale the pixel intensities from [0, 1] to [0, 255] when saving the part to the file
    cv2.imwrite(os.path.join(result_path, f'{image_channel}_{image_name}'), (U[1:h+1, 1:w+1]*255).astype(np.uint8))
    return os.path.join(result_path, f'{image_channel}_{image_name}')
