import os
import sys, argparse
import boto3
from Crypto.PublicKey import RSA


client = boto3.client('iot')


# python3 create_thing.py  -thing 2218724D  -type LUMINI  -policy FullAcces -output ../lumini5 
def getOptions(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Parses command.")
    parser.add_argument("-output", "--output", help="path folder output to save file certs_keys.h")
    parser.add_argument("-thing", "--thing", help="thing name")
    parser.add_argument("-type", "--type", help=" type (LUIMINI, IR or DIMMER).")
    parser.add_argument("-policy", "--policy", help="policy to attach")
    parser.add_argument("-v", "--verbose",dest='verbose',action='store_true', help="Verbose mode.")
    options = parser.parse_args(args)
    return options

if __name__ == "__main__":
    options = getOptions(sys.argv[1:])


    # create thing --------------------------------------------------------
    thingAws = client.create_thing(thingName=options.thing,thingTypeName=options.type)  
    if thingAws['ResponseMetadata']['HTTPStatusCode'] != 200: sys.exit('** Erro creating thing.')        

    # create certificate in aws cloud--------------------------------------
    certAws = client.create_keys_and_certificate(setAsActive=True)
    if certAws['ResponseMetadata']['HTTPStatusCode'] != 200: sys.exit('** Erro creating certs.')  

    # attach thing to principal (arn certificate)--------------------------
    certAttach = client.attach_thing_principal(thingName=options.thing,principal=certAws['certificateArn'])
    if certAttach['ResponseMetadata']['HTTPStatusCode'] != 200: sys.exit('** Erro creating on attach thing to certificate.')  

    # attach policy to principal (arn certificate)-------------------------
    policyAttach = client.attach_principal_policy(policyName=options.policy,principal=certAws['certificateArn'])
    if policyAttach['ResponseMetadata']['HTTPStatusCode'] != 200: sys.exit('** Erro creating on attach policy  to certificate.')  
    
    # get certs and keys --------------------------------------------------
    cert = certAws['certificatePem']
    privateKey = certAws['keyPair']['PrivateKey']
    publicKey = certAws['keyPair']['PublicKey']

    # convert to der cert and key------------------------------------------
    pathCert='{}.crt'.format(options.thing)
    pathKey='{}.key'.format(options.thing)
    with open(pathCert, 'w') as certFile:
        certFile.write('{}\n'.format(cert))
        certFile.close
    with open(pathKey, 'w') as keyFile:
        keyFile.write('{}\n'.format(privateKey))
        keyFile.close

    cmdConvertCert='openssl x509 -in  {}  -out cert.der -outform DER'.format(pathCert)
    cmdConvertKey='openssl rsa -in {} -out private.der -outform DER'.format(pathKey)

    os.system(cmdConvertCert)    
    os.system(cmdConvertKey)    

    # create file .h for arduino import -----------------------------------
    filePathH='{}/certs_keys.h'.format(options.output)
    if os.path.exists(filePathH):
        os.remove(filePathH)

    os.system('xxd -i {} >> {}'.format('cert.der',filePathH))
    os.system('xxd -i {} >> {}'.format('private.der',filePathH))
    os.system('xxd -i {} >> {}'.format('ca.der',filePathH))
    
    # remove certs and key -----------------------------------------------
    os.remove(pathCert)
    os.remove(pathKey)
    os.remove('cert.der')
    os.remove('private.der')
    
    print('certs_keys generate sucessfully!')

        


    # For delete certificate
    # certArn = 'arn:aws:iot:us-east-1:253112169656:cert/cd1623eb32356294c9571f2e5ebdd57650711548a881681bbce2dfbadefdfd44' 
    # certId=certArn.split('/')[1]
    # client.detach_thing_principal(thingName=options.thing,principal=certArn)
    # client.update_certificate(certificateId=certId,newStatus='INACTIVE')
    # client.delete_certificate(certificateId=certId,forceDelete=True)    
    