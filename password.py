import streamlit_authenticator as stauth
import sys

def generate_hash(password):
    """Gera o hash de uma senha para uso no config.yaml"""
    hash_pw = stauth.Hasher.hash(password)
    print(f"\nSenha: {password}")
    print(f"Hash: {hash_pw}\n")
    print("Copie o Hash acima e cole no seu arquivo config.yaml")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Se passar a senha como argumento: python generate_hash.py minha_senha
        generate_hash(sys.argv[1])
    else:
        # Caso contrário, pede input
        password = input("Digite a senha que deseja transformar em Hash: ")
        generate_hash(password)
