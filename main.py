import glob
import os
import cv2
from tqdm import tqdm


def attributes():
	start_pos, end_pos, resize_factor, duration = [], [], 0, 0

	try:
		start_pos = input("Enter start position (Ex: 0,0): ").split(",")
		end_pos = input("Enter start position (Ex: 2000,2000): ").split(",")

		start_pos = (int(start_pos[0]), int(start_pos[1]))
		end_pos = (int(end_pos[0]), int(end_pos[1]))

		resize_factor = int(input("Resolution Multiplication (Recommended: 5-10): "))
		duration = int(input("Duration (In Seconds): "))

	except ValueError:
		print("Invalid input, must be formatted as 'x,y'")
		exit()
	except IndexError:
		print("Invalid input, must be formatted as 'x,y'")
		exit()

	if start_pos[0] > end_pos[0] or start_pos[1] > end_pos[1]:
		print("Ending Position must be greater than Starting Position")
		exit()

	return start_pos, end_pos, resize_factor, duration


def crop_image(image, start_pos, end_pos, index):
	if image.endswith(".png"):
		img = cv2.imread("./images/" + image)
		img = img[start_pos[1]:end_pos[1], start_pos[0]:end_pos[0]]
		cv2.imwrite("./cropped/" + str(index) + ".png", img)


def main():
	# Check that we have Cisco Openh264 DLL installed in the script directory
	if not os.path.exists("./openh264-1.8.0-win64.dll"):
		# Ask user for permission to download OpenH264 DLL
		download = input("OpenH264 DLL not found, would you like to automatically download it from https://github.com/cisco/openh264/releases/tag/v1.8.0 ? (Y/n): ")
		if download.lower() != "y" and download.lower() != "":
			# Give instructions on how to download OpenH264 DLL
			print("Please download OpenH264 DLL from https://github.com/cisco/openh264/releases/tag/v1.8.0, unpack it, and place it in the same directory as this script")
			exit()

		# Download OpenH264 DLL from GitHub and unpack it into working directory
		import requests
		import bz2

		print(f"Downloading OpenH264 from https://github.com/cisco/openh264/releases/download/v1.8.0/openh264-1.8.0-win64.dll.bz2...")
		r = requests.get(f"https://github.com/cisco/openh264/releases/download/v1.8.0/openh264-1.8.0-win64.dll.bz2")
		if r.status_code != 200:
			print(r.raise_for_status())
			exit()
		open(f"openh264-1.8.0-win64.dll.bz2", 'wb').write(r.content)
		print("Extracting...")
		zip_data = bz2.BZ2File(f"openh264-1.8.0-win64.dll.bz2").read()
		open(f"openh264-1.8.0-win64.dll", 'wb').write(zip_data)
		os.remove(f"openh264-1.8.0-win64.dll.bz2")

	if not os.path.exists("./images"):
		os.makedirs("./images")

	if not os.path.exists("./cropped"):
		os.makedirs("./cropped")

	if len(os.listdir("./images")) == 0:
		print("No images found, please place images in ./images")
		download = input("Would you like to automatically download and unpack images from https://zevs.me/rplace_archive.7z (10.6GB)? (Y/n): ")
		if download != "y" and download != "":
			print("Please download images from https://zevs.me/rplace_archive.7z (Or elsewhere), and unpack them in ./images directory\n(Note: zevs.me archive has a subdirectory. Do not include this subdirectory in ./images)")
			exit()

		# Download images from zevs.me and unpack them to ./images
		import requests
		from py7zr import unpack_7zarchive
		import shutil

		# Download archive
		if not os.path.exists("./rplace_archive.7z"):
			print("Downloading images from https://zevs.me/rplace_archive.7z... This may take awhile...")
			r = requests.get("https://zevs.me/rplace_archive.7z")
			if r.status_code != 200:
				print(r.raise_for_status())
				exit()
			open("./rplace_archive.7z", 'wb').write(r.content)

		# Unpack archive
		print("Extracting... This may take awhile...")
		shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)
		shutil.unpack_archive('./rplace_archive.7z', './images')

	# Get the attributes from the user
	start_pos, end_pos, resize_factor, duration = attributes()

	# Get the video dimensions
	frame_width = end_pos[0] - start_pos[0]
	frame_height = end_pos[1] - start_pos[1]

	# Create out video output
	out = cv2.VideoWriter("./final.mp4", cv2.VideoWriter_fourcc(*'avc1'), round(len(os.listdir("./images"))/duration), (frame_width * resize_factor, frame_height * resize_factor))

	# Iterate through the images in ./images and crop them to ./cropped
	length = len(os.listdir("./images"))
	with tqdm(total=length, desc="Cropping images...") as bar:
		for index, image in enumerate(sorted(os.listdir("./images"))):
			crop_image(image, start_pos, end_pos, index)
			bar.update()

	image_list = sorted(glob.glob("./cropped/*.png"), key=len)

	# Iterate through the images in ./cropped and resize them to the video dimensions multiplied by our resize factor and add them to our output
	length = len(image_list)
	with tqdm(total=length, desc="Creating video...") as bar:
		for image in image_list:
			image_frame = cv2.imread(image)
			resized = cv2.resize(image_frame, (frame_width * resize_factor, frame_height * resize_factor), interpolation=cv2.INTER_NEAREST)
			out.write(resized)
			bar.update()

	out.release()

	# Delete the cropped images from ./cropped
	print("Done! Cleaning up files...")
	for image in os.listdir("./cropped"):
		os.remove("./cropped/" + image)

	print("Done cleaning up files! It was fun creating a /r/Place with you!")


if __name__ == "__main__":
	main()
