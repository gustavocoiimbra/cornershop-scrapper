from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import re

browser = 0

def iniciarNavegador(show: bool,
                     raspSimp: bool,
                     raspComp: bool,
                     CEP: int):
    """
    Está função abrirá o navegador com as configurações solicitadas.

    :param show: False -> executa o navegador em modo anônimo.
                 True -> executa o navegador normalmente.

    :param raspSimp: Raspagem Simples -> irá raspar os dados da página inicial.

    :param raspComp: Raspagem Completa -> irá raspar os dados da aba "CORREDORES"
    percorrendo departamento por departamento.
    """
    global browser

    optionsBrowser = Service(ChromeDriverManager().install())
    optionsService = Options()

    # Executa o navegador normalmente maximizado
    if show:
        driver = webdriver.Chrome(service=optionsBrowser, options=optionsService)
        driver.maximize_window()

    # Executa o navegador em modo anônimo
    else:
        optionsService.add_argument('--headless')
        driver = webdriver.Chrome(service=optionsBrowser, options=optionsService)

    # Abrindo o navegador
    with driver as browser:

        browser.get("https://web.cornershopapp.com/")

        # Chama a função que irá entrar no site e preencher o CEP
        entrarSite(CEP=CEP)

        if raspSimp:
            acessarSupermercados()

        if raspComp:
            extrairLinks()

        browser.quit()

    return 1


def entrarSite(CEP: int):
    """
    Esta função encontra o campo para preencher o CEP e o botão 'Feito'.
    """
    global browser

    # Caso não seja necessário preencher com o CEP retorna para função iniciarNavegador.
    try:
        WebDriverWait(browser, timeout=10).until(
            lambda x: x.find_element(By.XPATH, '//*[@id="modal-container"]'
                                               '/div[2]/div/div/div/div[2]/div/button[1]')).click()

        WebDriverWait(browser, timeout=10).until(
            lambda x: x.find_element(By.XPATH, '//input [@id="zip-code-input"]')).send_keys(CEP)

        browser.find_element(By.XPATH,
                             '//*[@id="modal-container"]/div[2]/div/div[1]/div/div[3]/button').click()

    except TimeoutException:
        print("Não foi necessário inserir o CEP!")

    return


def extrairLinks():
    """
    Está função é usada somente para realizar a Raspagem Completa.
    O código acessa todos os Supermercados e extrai o link da página web.
    """

    allLinks = list()

    allStores = WebDriverWait(browser, timeout=10).until(
        lambda x: x.find_elements(By.XPATH, '//*[@id="app-container"]/main/div/section[1]/'
                                            'section/div/figure/div/figure/div/button'))
    allStores = len(allStores)

    # Os dois ‘loops’ a seguir serão usados para indicar qual supermercado será acessado
    for store in range(1, int(allStores / 2) + 1):
        for i in range(1, 3):

            # Tenta encontrar o elemento do supermercado e clicar para acessa-lo
            try:
                button_supermarket = WebDriverWait(browser, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, f'//*[@id="app-container"]/main/div/section['
                                                              f'1]/section/div/figure[{store}] '
                                                              f'/div/figure[{i}]/div/button')))
                button_supermarket.click()

            # Caso o elemento para acessar o supermercado esteja "coberto" elemento 'button-next'
            #  a página será atualizada e receberá o click para que o 'button_supermarket' receba o click
            except ElementClickInterceptedException:
                try:
                    browser.refresh()
                    button = WebDriverWait(browser, timeout=10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="app-container"]/main/div/section['
                                                                  '1]/section/button[2]')))
                    button.click()

                    button_supermarket = WebDriverWait(browser, timeout=1).until(
                        EC.presence_of_element_located((By.XPATH, f'//*[@id="app-container"]/main/div/section['
                                                                  f'1]/section/div/figure[{store}] '
                                                                  f'/div/figure[{i}]/div/button')))
                    button_supermarket.click()

                except TimeoutException or ElementClickInterceptedException:
                    continue

            # Extrai o link da página e adiciona à lista
            allLinks.append(browser.current_url)
            browser.back()

    acessarLinks(linksStores=allLinks)


def acessarLinks(linksStores: list):

    """
    O programa acessa o 'link' de cada Supermercado em nova aba do navegador e
    acessa a aba "corredor" da página.
    """

    # Abrindo uma nova aba no navegador
    browser.execute_script(f"window.open('', '_blank')")

    # Loop para acessar todos os supermercados e extrair o link
    for url in linksStores:
        browser.switch_to.window(browser.window_handles[1])
        browser.get(url)

        corredor = WebDriverWait(browser, timeout=10).until(
            lambda x: x.find_element(By.XPATH, '//*[@id="app-container"]/header/div[3]/div/div[2]/input'))

        corredor.click()

        # Vamos percorrer todos os departamentos
        acessarDepartamentos()


def acessarSupermercados():
    """ O programa abaixo serve para determinar quantos Supemercados estão na página inicial do site e
    entra numa loja por vez."""
    global browser

    # Seleciona todos os mercados da página inicial
    allStores = WebDriverWait(browser, timeout=10).until(
        lambda x: x.find_elements(By.XPATH, '//*[@id="app-container"]/main/div/section[1]/'
                                            'section/div/figure/div/figure/div/button'))
    browser.find_elements(By.CLASS_NAME, 'store-acess')

    allStores = len(allStores)

    # Os dois ‘loops’ a seguir serão usados para indicar qual supermercado será acessado
    for store in range(1, int(allStores / 2) + 1):
        for i in range(1, 3):

            # Tenta acessar o botão correspondente ao supermercado
            try:
                # Tenta acessar o botão correspondente ao supermercado
                button_supermarket = WebDriverWait(browser, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, f'//*[@id="app-container"]/main/div/section['
                                                              f'1]/section/div/figure[{store}] '
                                                              f'/div/figure[{i}]/div/button')))
                button_supermarket.click()

            except ElementClickInterceptedException or TimeoutException:
                # Caso o elemento para acessar o supermercado esteja "coberto" elemento 'button-next'
                #  a página será atualizada e receberá o click para que o 'button_supermarket' receba o click
                try:
                    browser.refresh()
                    button = WebDriverWait(browser, timeout=10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="app-container"]/main/div/section['
                                                                  '1]/section/button[2]')))
                    button.click()

                    sleep(1)

                    button_supermarket = WebDriverWait(browser, timeout=1).until(
                        EC.presence_of_element_located((By.XPATH, f'//*[@id="app-container"]/main/div/section['
                                                                  f'1]/section/div/figure[{store}] '
                                                                  f'/div/figure[{i}]/div/button')))
                    button_supermarket.click()

                except TimeoutException or ElementClickInterceptedException:
                    continue

            # Fazendo o scroll na página para carregar os produtos
            salvar = scroll()

            if salvar:
                # Salvando os dados
                scrapping_And_save()

            # Retornando para a primeira aba e retornando para a página principal

            sleep(0.5)
            browser.back()

    return


def acessarDepartamentos():
    """
    O código encronta o botão "Todos os produtos em ...."  e entra no departamento.
    """

    allDepartments = list()
    allPrices = list()
    allProducts = list()
    allPackages = list()

    numberDeps = WebDriverWait(browser, timeout=10).until(
        lambda x: x.find_elements(By.XPATH, f'//*[@id="app-container"]/main/div/div/div/div[2]/div[1]/div'))

    numberDeps = len(numberDeps)

    # Acessando departamento por departamento
    for depart in range(1, numberDeps + 1):
        button = WebDriverWait(browser, timeout=10).until(lambda x: x.find_element(
            By.XPATH, f'//*[@id="app-container"]/main/div/div/div[{depart}]/div[2]/div[1]/div'))

        nameDepartment = browser.find_element(By.XPATH,
                                              f'//*[@id="app-container"]/main/div/div/div[{depart}]/'
                                              f'div[2]/div[1]/div/div[1]/p')
        nameDepartment = nameDepartment.text

        # Entrando no departamento
        button.click()

        # Fazendo o scroll na página para carregar todos os produtos
        salvar = scroll()

        if salvar:
            # Salvando os dados
            save(nameDepartment,
                 dep=allDepartments,
                 preco=allPrices,
                 prod=allProducts,
                 pack=allPackages)

        # Voltando para página corredores
        browser.switch_to.window(browser.window_handles[1])
        back = browser.find_element(By.XPATH, f'//*[@id="app-container"]/nav/div[1]/button')
        back.click()

    allList = list(zip(allDepartments, allProducts, allPrices, allPackages))
    store_name = browser.find_element(By.XPATH, f'//*[@id="app-container"]/nav/h1')
    df = pd.DataFrame(allList)
    df.insert(0, "Supermercado", f"{store_name.text}")
    file_name = f'TodosDadosSupermercado{store_name.text}.csv'
    df.to_csv(file_name)

    formatarDados(supermercado=store_name,
                  raspComp=True,
                  raspSimp=False)


def scroll():
    """
    Está função faz a rolagem da página para que todos os produtos
    sejam carregados.
    """
    try:
        # Espera até que apareça os produtos na página
        WebDriverWait(browser, timeout=10).until(
            lambda x: x.find_elements(By.XPATH, f'//*[@class="product"]'))

    except TimeoutException:
        # Como algumas páginas ao abrir apresentam erro para carregar os produtos, o programa
        # irá abrir uma nova aba para tentar carregar a página.
        try:
            urlFalha = browser.current_url
            browser.execute_script(f"window.open('', '_blank')")
            browser.switch_to.window(browser.window_handles[2])
            browser.get(urlFalha)

            WebDriverWait(browser, timeout=10).until(
                lambda x: x.find_elements(By.XPATH, f'//*[@class="product"]'))

        # Caso o erro de não apresentar nenhum item na página permaneça o programa
        # retorna para página anterior e dá continuidade a raspagem de outros departamentos
        except TimeoutException:
            browser.switch_to.window(browser.window_handles[0])
            return False

    # Encontra o tamanho da página
    sleep(1.5)
    startPag = 0
    endPag = browser.execute_script("return document.body.scrollHeight")

    while True:

        # Faz a rolagem do ínicio até o fim da página
        [browser.execute_script(f"window.scrollTo(0, {mouse})") for mouse in range(startPag, endPag, 25)]

        sleep(0.5)
        # Encontra novamente o tamanho da página
        NewEndPag = browser.execute_script("return document.body.scrollHeight")

        # Caso a página continue aumentando de tamanho o loop continua
        if endPag != NewEndPag:
            startPag = endPag
            endPag = NewEndPag
            continue

        # O loop while é encerrado quando a página chega ao fim
        else:
            # Retorna para o ínicio da página
            [browser.execute_script(f"window.scrollTo(0, {mouse})") for mouse in range(endPag, 0, -100)]
            break

            # browser.switch_to.window(browser.window_handles[0])

    return True


def scrapping_And_save():
    # Salvando os dados
    page = browser.page_source
    site = BeautifulSoup(page, 'html.parser')
    departments = site.findAll(class_="department-box card")

    allDepartments = list()
    allPrices = list()
    allProducts = list()
    allPackages = list()

    for depart in departments:
        nameDepartment = depart.findAllNext('h2')[0]
        for prod in depart.findAll(class_="product-info"):
            name = prod.find(class_="name")
            price = prod.find(class_="price")
            package = prod.find(class_="package") if (prod.find(class_="package")) is not None \
                else prod.find(class_="color-white")

            allDepartments.append(nameDepartment.text), allProducts.append(name.text)
            allPrices.append(price.text), allPackages.append(
                package.text if package is not None else "None")

    lista = list(zip(allDepartments, allProducts, allPrices, allPackages))

    name_supermarket = site.find(class_="title")
    df = pd.DataFrame(lista)
    df.insert(0, "Supermercado", f"{name_supermarket.text}")
    file_name = f'DadosSupermercado{name_supermarket.text}.csv'
    df.to_csv(file_name)

    formatarDados(supermercado=name_supermarket,
                  raspComp=False,
                  raspSimp=True)


def save(name: str,
         dep: list,
         prod: list,
         preco: list,
         pack: list):

    page = browser.page_source
    site = BeautifulSoup(page, 'html.parser')
    products = site.findAll(class_="product-info")

    for product in products:
        name_prd = product.find(class_="name")
        price = product.find(class_="price")
        package = product.find(class_="package") if (product.find(class_="package")) is not None \
            else product.find(class_="color-white")

        dep.append(name), prod.append(name_prd.text)
        preco.append(price.text), pack.append(package.text if package is not None else "None")


def formatarDados(supermercado,
                  raspComp: bool,
                  raspSimp: bool):

    def slipt(preco: str, nova_coluna=False, excluir_var=False):
        preco = re.split('\s', preco)
        if nova_coluna:
            if len(preco) == 3:
                return preco[2]
            else:
                return "0"
        if excluir_var:
            return preco[1]

    supermercado = supermercado.text

    if raspSimp:
        df = pd.read_csv(f"DadosSupermercado{supermercado}.csv", sep=',')

        # Excluindo dados duplicados
        df.drop_duplicates(keep="first", inplace=True)

        # Renomeando as colunas
        colunas = {"0": "Departamento", "1": "Produto", "2": "Preco", "3": "Detalhes"}
        df.rename(columns=colunas, inplace=True)

        # Excluindo a coluna
        df.drop(["Unnamed: 0"], axis=1, inplace=True)

        # Criando a coluna que irá armazenar valores antigos
        df["Preco_Antigo"] = "0"

        # Ordenando as colunas
        df = df[["Supermercado", "Departamento", "Produto", "Preco", "Preco_Antigo", "Detalhes"]]

        # Retirando os caracteres especiais da coluna "Preco"
        df["Preco"] = df["Preco"].str.replace('\$', '').str.replace('R', '').str.replace(',', '.')

        # Preenchendo a coluna "Preco_Antigo" e excluindo os valores duplicados da coluna "Preco"
        df["Preco_Antigo"] = df["Preco"].apply(lambda x: slipt(x, nova_coluna=True, excluir_var=False))
        df["Preco"] = df["Preco"].apply(lambda x: slipt(x, nova_coluna=False, excluir_var=True))

        file_name = f'DadosSupermercado{supermercado}.csv'
        df.to_csv(file_name)

    if raspComp:
        df = pd.read_csv(f"TodosDadosSupermercado{supermercado}.csv", sep=',')

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)

        # Excluindo dados duplicados
        df.drop_duplicates(keep="first", inplace=True)

        # Renomeando as colunas
        colunas = {"0": "Departamento", "1": "Produto", "2": "Preco", "3": "Detalhes"}
        df.rename(columns=colunas, inplace=True)

        # Criando a coluna que irá armazenar valores antigos
        df["Preco_Antigo"] = "0"

        # Ordenando as colunas
        df = df[["Supermercado", "Departamento", "Produto", "Preco", "Preco_Antigo", "Detalhes"]]

        # Retirando os caracteres especiais da coluna "Preco"
        df["Preco"] = df["Preco"].str.replace('\$', '').str.replace('R', '').str.replace(',', '.')

        # Preenchendo a coluna "Preco_Antigo" e excluindo os valores duplicados da coluna "Preco"
        df["Preco_Antigo"] = df["Preco"].apply(lambda x: slipt(x, nova_coluna=True, excluir_var=False))
        df["Preco"] = df["Preco"].apply(lambda x: slipt(x, nova_coluna=False, excluir_var=True))

        file_name = f'TodosDadosSupermercado{supermercado}.csv'
        df.to_csv(file_name)

    return


if __name__ == '__main__':

    iniciarNavegador(show=True,
                     raspSimp=True,
                     raspComp=False,
                     CEP=74351020)