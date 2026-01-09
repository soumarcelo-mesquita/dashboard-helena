//https://helena.readme.io/reference/getting-started-with-your-api

const tags = {
    "b9fd9d2f-205e-48bc-bd9c-d567a5caff46": "258",
    "ed25b37f-0426-4a38-bf58-8cd52bd7bdf3": "439",
    "ec87f87c-dee5-4f32-940d-f9904c6280ed": "CARPH",
    "6406f480-913f-4f09-9c8b-59605ba9be1c": "FUNASA",
    "a3baba0d-92ae-41b4-8d2e-5552a4a391b6": "COHAB",
    "ee45009a-11ad-47db-82c0-c6ede2d45ebb": "Correios",
    "83ee3bbc-6dfe-42ee-a1cc-6ad0bcc4efab": "EMATER",
    "b3b54f36-3466-4414-a512-608e0b983434": "Falecido",
    "9632656d-542a-427a-9b77-beee485408d9": "GIFA TRF1",
    "f01c85f0-9525-437f-ab31-93802c6d22d4": "individualizado",
    "5b731f14-159c-45c0-8f57-d183ca5ec45a": "JFAL",
    "d93fb9a2-335e-46e9-9976-55ab2c849627": "JFCE",
    "465efcf4-d3d0-40c9-9f18-c11a8c78e57c": "JFPB",
    "a6727a87-ef2b-4d05-a7d3-bac8b84b7176": "JFPE",
    "14872625-5dc1-4ab7-8c7d-43f575a32bc5": "JFRN",
    "03697211-7c15-4fd4-97d6-ba67fd5e6277": "PRC Federais",
    "1c5db88e-305e-41a5-971f-dc532f35f928": "refazer pesquisa",
    "612c0156-29cf-4cf5-93ce-427c11e6fc07": "SERVEAL"
}


const steps = {
    'Prospecção': '5174b630-1faf-43e7-b027-a4c82c5f0711',
    'Em contato': '3868b730-4209-4b1c-849a-fe86decb528b',
    '48h': 'fac6da90-ab58-43b3-8d0e-0add15f08b9a',
    'Reunião': '88cf5d3b-c776-40c2-9d8d-e0d1ca4eab23',
    'Proposta enviada': '3450c042-fc9a-4bcf-bc34-ad8fec9e04f1',
    'Documentação': '6e54e8fd-ebfb-44eb-b665-d6b42e62ad9f',
    'Peticionamento': '0f9962b6-a632-46bc-a99e-a4916d004d4a',
    'Concluído': '18da2de7-640b-4792-8ae4-f5ba9b1ff04c',
    'No Deal': '47c40d05-4da7-42d6-9040-b2624079ad7b'
}

const token = 'pn_MYErHyZDGRcYqaa7zFjziA3zYfr3PR8GendModNpk4'
const panelId = '3a2aa62a-2678-490a-93b3-369fe441eaaf'

function getCards() {
    const ss = SpreadsheetApp.getActiveSpreadsheet()
    const sheet = ss.getSheetByName('Dados')

    let hasMorePages = true
    let pageNumber = 1

    while (hasMorePages) {
        try {

            const url = `https://api.helena.run/crm/v1/panel/card?PanelId=${panelId}&PageNumber=${pageNumber}&PageSize=10&IncludeDetails=StepTitle`
            const options = {
                'method': 'GET',
                'headers': { 'accept': 'application/json', 'Authorization': token }
            }

            const response = UrlFetchApp.fetch(url, options)
            const json = JSON.parse(response)
            const values = json.items.map(parseCard)
            sheet.getRange(sheet.getLastRow() + 1, 1, values.length, values[0].length).setValues(values)

            hasMorePages = json.hasMorePages
            pageNumber++

        } catch (e) {
            console.log(e)
        }

    }
}

const parseCard = function (card) {
    let tags = card.tagIds.map(parseTags)
    return [
        card.id,
        new Date(card.createdAt),
        new Date(card.updatedAt),
        card.title,
        card.stepTitle,
        getActionType(tags),
        card.monetaryAmount,
        tags.join(', '),
        getAgingGroup(card.updatedAt)
    ]
}

function getAgingGroup(updatedAt) {
    const days = diffInDays(updatedAt);

    if (days === 0) return "Hoje";
    if (days <= 2) return "48 horas";
    if (days <= 7) return "7 dias";
    if (days <= 15) return "15 dias";

    return "Mais de 15 dias";
}

function diffInDays(dateString) {
    const updatedAt = new Date(dateString);
    const now = new Date();

    const diffMs = now - updatedAt;
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

const parseTags = function (tagId) {
    return tags[tagId]
}

const getActionType = function (tagIds) {
    if (tagIds.includes('258')) return '258'
    if (tagIds.includes('439')) return '439'
    if (tagIds.includes('FUNASA')) return 'FUNASA'
    if (tagIds.includes('CARPH')) return 'CARPH'
    return ''
}