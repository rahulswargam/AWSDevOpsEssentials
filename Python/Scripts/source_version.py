import json
import sys

def update_source_version(json_file, client_name, instance_type, new_version):
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)

        # Update the source version where client_name and instance_type match
        for project in data:
            if project['client_name'] == client_name and project['instance_type'] == instance_type:
                project['source_version'] = new_version

        with open(json_file, 'w') as file:
            json.dump(data, file, indent=4)

        print(f"Updated {json_file} successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python update_source_version.py <client_name> <instance_type> <new_source_version>")
    else:
        _, client_name, instance_type, new_version = sys.argv
        update_source_version("projects.json", client_name, instance_type, new_version)
