import oci
from functions import create_signer
import json
from datetime import datetime, timedelta
import os
import time

shapes = [
    #"BM.DenseIO.52",
    "BM.DenseIO.E4.128",
    "BM.DenseIO.E5.128",
    "BM.Standard2.52",
    "BM.Standard3.64",
    "BM.Standard.E4.128",
    "BM.Standard.E5.192",
    "BM.GPU.A10.4"  
]


ADs = [
    "UK-LONDON-1-AD-1",
    "UK-LONDON-1-AD-2",
    "UK-LONDON-1-AD-3",
    "UK-CARDIFF-1-AD-1",
    "EU-FRANKFURT-1-AD-1",
    "EU-FRANKFURT-1-AD-2",
    "EU-FRANKFURT-1-AD-3",
    "EU-AMSTERDAM-1-AD-1",
    "EU-PARIS-1-AD-1",
    "EU-MARSEILLE-1-AD-1",
    "EU-STOCKHOLM-1-AD-1", 
    "EU-MADRID-1-AD-1",  
    "EU-MILAN-1-AD-1",
    "EU-ZURICH-1-AD-1",
    "ME-ABUDHABI-1-AD-1", 
    "ME-DUBAI-1-AD-1",
    "ME-JEDDAH-1-AD-1",
    "ME-RIYADH-1-AD-1",  
    "IL-JERUSALEM-1-AD-1" 
]

FDs = ["FAULT-DOMAIN-1","FAULT-DOMAIN-2","FAULT-DOMAIN-3"]

configfile = "~/.oci/config"  # Linux
configProfile = "DEFAULT"

config, signer = create_signer(configProfile, False, False)

identity = oci.identity.IdentityClient(config, signer=signer)
compute = oci.core.ComputeClient(config, signer=signer)
tenancy = identity.get_tenancy(config['tenancy']).data
print ("Tenancy: {} - {}".format(tenancy.name, tenancy.id))


# "availability_status": "AVAILABLE"
# "availability_status": "OUT_OF_HOST_CAPACITY"
# "availability_status": "HARDWARE_NOT_SUPPORTED"


def load_existing_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load existing data from {file_path}: {e}")
            return {}
    return {}


def save_data(file_path, data):
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")
        raise


def clean_old_data(data, days=31):
    if not data:  # If data is empty, return it as is
        return data
    cutoff_date = datetime.now() - timedelta(days=days)
    return {date: info for date, info in data.items() if datetime.strptime(date, '%Y-%m-%d') >= cutoff_date}


def serialize_report_data(shape_availabilities):
    # Convert the shape availabilities into a dictionary format
    # shape_availabilities is a list of fault domain availability data
    result = {
        'fault_domains': {}
    }
    
    for availability in shape_availabilities:
        fault_domain = availability.fault_domain
        result['fault_domains'][fault_domain] = {
            'availability_status': availability.availability_status,
            'available_count': availability.available_count,
            'instance_shape': availability.instance_shape,
            'instance_shape_config': availability.instance_shape_config
        }
    
    return result


def main():
    file_path = 'capacity_report.json'
    print(f"Loading existing data from {file_path}...")
    existing_data = load_existing_data(file_path)
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"Processing data for date: {today_str}")

    # Clean old data
    existing_data = clean_old_data(existing_data)

    # Prepare today's data
    today_data = {}
    for AD in ADs:
        config["region"] = AD.split("-AD-")[0].lower()
        compute = oci.core.ComputeClient(config, signer=signer)
        print ("Gettting capacity for [{}] {}".format(config["region"],AD),end="", flush=True)

        response = oci.pagination.list_call_get_all_results(
            oci.identity.IdentityClient(config, signer=signer, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY).list_availability_domains,
            compartment_id=tenancy.id
        )
        avail_domain = "{}:{}".format(response.data[0].name.split(":")[0], AD)
        print ("Region prefix: {}".format(avail_domain),end="", flush=True)

        ad_data = {}
        for shape in shapes:
            print(".", end="", flush=True)
            report_details = oci.core.models.CreateComputeCapacityReportDetails(
                compartment_id=tenancy.id,
                availability_domain=avail_domain,
                shape_availabilities=[
                    oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                        instance_shape=shape,
                        fault_domain=FD,
                        instance_shape_config=None
                    ) for FD in FDs
                ]
            )

            report = compute.create_compute_capacity_report(create_compute_capacity_report_details=report_details, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            ad_data[shape] = serialize_report_data(report.data.shape_availabilities)

        today_data[AD] = ad_data
        print ("",end="\n", flush=True)
        time.sleep(2)

    # Update today's data
    existing_data[today_str] = today_data

    # Save updated data
    save_data(file_path, existing_data)


if __name__ == "__main__":
    main()

