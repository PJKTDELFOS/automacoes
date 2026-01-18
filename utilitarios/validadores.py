class Validadores:

    @staticmethod
    def validador_cpf(cpf:str)->bool:  #type: ignore
        if len(set(cpf))==1:return False

        soma=sum(int(cpf[i]) *(10-i) for i in range(9))
        d1=(soma*10%11)%10
        if d1 !=int(cpf[9]):return False

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        d2 = (soma * 10 % 11) % 10
        return d2==int(cpf[10])

    @staticmethod
    def validar_cnpj(cnpj:str)->bool:  #type: ignore
        if len(set(cnpj))==1:return False

        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        soma=sum(
            int(cnpj[i]) *pesos_1[i] for i in range(12)
        )
        d1=11-(soma%11)
        d1=0 if d1>=10 else d1
        if d1!=int(cnpj[12]):return False

        soma = sum(
            int(cnpj[i]) * pesos_2[i] for i in range(13)
        )
        d2 = 11 - (soma % 11)
        d2 = 0 if d2 >= 10 else d2
        return d2==int(cnpj[13])



