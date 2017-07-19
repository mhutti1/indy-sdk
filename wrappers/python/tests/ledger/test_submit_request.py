from tests.utils import pool, storage
from tests.utils.wallet import create_and_open_wallet
from indy import ledger, wallet, signus
from indy.pool import close_pool_ledger
from indy.error import ErrorCode, IndyError

import json
import pytest
import logging

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(autouse=True)
def before_after_each():
    storage.cleanup()
    yield
    storage.cleanup()


@pytest.fixture
async def wallet_handle():
    handle = await create_and_open_wallet()
    yield handle
    await wallet.close_wallet(handle)


@pytest.fixture
async def pool_handle():
    handle = await pool.create_and_open_pool_ledger("pool_1")
    yield handle
    await close_pool_ledger(handle)


@pytest.mark.asyncio
async def test_submit_request_works(pool_handle):
    request = {
        "reqId": 1491566332010860,
        "identifier": "Th7MpTaRZVRYnPiabds81Y",
        "operation": {
            "type": "105",
            "dest": "Th7MpTaRZVRYnPiabds81Y"
        },
        "signature": "4o86XfkiJ4e2r3J6Ufoi17UU3W5Zi9sshV6FjBjkVw4sgEQFQov9dxqDEtLbAJAWffCWd5KfAk164QVo7mYwKkiV"
    }

    expected_response = {
        "result": {
            "reqId": 1491566332010860,
            "identifier": "Th7MpTaRZVRYnPiabds81Y",
            "dest": "Th7MpTaRZVRYnPiabds81Y",
            "data": "{\"dest\":\"Th7MpTaRZVRYnPiabds81Y\",\"identifier\":\"V4SGRU86Z58d6TV7PBUe6f\",\"role\":\"2\""
                    ",\"verkey\":\"~7TYfekw4GUagBnBVCqPjiC\"}",
            "type": "105",
        },
        "op": "REPLY"
    }
    response = json.loads((await ledger.submit_request(pool_handle, json.dumps(request))).decode())
    assert response == expected_response


@pytest.mark.asyncio
async def test_submit_request_works_for_invalid_pool_handle(pool_handle, wallet_handle):
    (my_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                          '{"seed":"000000000000000000000000Trustee1"}')

    get_nym_request = await ledger.build_get_nym_request(my_did.decode(), my_did.decode())
    invalid_pool_handle = pool_handle + 1
    try:
        await ledger.submit_request(invalid_pool_handle, get_nym_request.decode())
        raise Exception("Failed")
    except Exception as e:
        assert type(IndyError(ErrorCode.PoolLedgerInvalidPoolHandle)) == type(e) and \
               IndyError(ErrorCode.PoolLedgerInvalidPoolHandle).args == e.args


@pytest.mark.asyncio
async def test_send_nym_request_works_without_signature(pool_handle, wallet_handle):
    (my_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                          '{"seed":"00000000000000000000000000000My1"}')

    nym_request = await ledger.build_nym_request(my_did.decode(), my_did.decode(), None, None, None)
    try:
        await ledger.submit_request(pool_handle, nym_request.decode())
        raise Exception("Failed")
    except Exception as e:
        assert type(IndyError(ErrorCode.LedgerInvalidTransaction)) == type(e) and \
               IndyError(ErrorCode.LedgerInvalidTransaction).args == e.args


@pytest.mark.asyncio
async def test_send_get_nym_request_works(pool_handle, wallet_handle):
    (my_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                          '{"seed":"000000000000000000000000Trustee1"}')

    get_nym_request = await ledger.build_get_nym_request(my_did.decode(), my_did.decode())

    response = json.loads((await ledger.submit_request(pool_handle, get_nym_request.decode())).decode())
    assert response['result']['data'] is not None


@pytest.mark.asyncio
async def test_nym_requests_works(pool_handle, wallet_handle):
    (trustee_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                               '{"seed":"000000000000000000000000Trustee1"}')
    (my_did, my_ver_key, _) = await signus.create_and_store_my_did(wallet_handle,
                                                                   '{"seed":"00000000000000000000000000000My1"}')

    nym_request = await ledger.build_nym_request(trustee_did.decode(), my_did.decode(), my_ver_key.decode(), None, None)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did.decode(), nym_request.decode())
    get_nym_request = await ledger.build_get_nym_request(my_did.decode(), my_did.decode())
    response = json.loads((await ledger.submit_request(pool_handle, get_nym_request.decode())).decode())
    assert response['result']['data'] is not None


@pytest.mark.asyncio
async def test_send_attrib_request_works_without_signature(pool_handle, wallet_handle):
    (my_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                          '{"seed":"00000000000000000000000000000My1"}')

    attrib_request = await ledger.build_attrib_request(my_did.decode(), my_did.decode(), None,
                                                       "{\"endpoint\":{\"ha\":\"127.0.0.1:5555\"}}", None)
    try:
        await ledger.submit_request(pool_handle, attrib_request.decode())
        raise Exception("Failed")
    except Exception as e:
        assert type(IndyError(ErrorCode.LedgerInvalidTransaction)) == type(e) and \
               IndyError(ErrorCode.LedgerInvalidTransaction).args == e.args


@pytest.mark.asyncio
async def test_attrib_requests_works(pool_handle, wallet_handle):
    (trustee_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                               '{"seed":"000000000000000000000000Trustee1"}')
    (my_did, my_ver_key, _) = await signus.create_and_store_my_did(wallet_handle,
                                                                   '{"seed":"00000000000000000000000000000My1"}')
    nym_request = await ledger.build_nym_request(trustee_did.decode(), my_did.decode(), my_ver_key.decode(), None, None)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did.decode(), nym_request.decode())
    attrib_request = await ledger.build_attrib_request(my_did.decode(), my_did.decode(), None,
                                                       "{\"endpoint\":{\"ha\":\"127.0.0.1:5555\"}}", None)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, my_did.decode(), attrib_request.decode())
    get_attrib_request = await ledger.build_get_attrib_request(my_did.decode(), my_did.decode(), "endpoint")
    response = json.loads((await ledger.submit_request(pool_handle, get_attrib_request.decode())).decode())
    assert response['result']['data'] is not None


@pytest.mark.asyncio
async def test_send_schema_request_works_without_signature(pool_handle, wallet_handle):
    (my_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                          '{"seed":"00000000000000000000000000000My1"}')

    schema_data = {
        "name": "gvt2",
        "version": "2.0",
        "keys": ["name", "male"]
    }

    schema_request = await ledger.build_schema_request(my_did.decode(), json.dumps(schema_data))

    try:
        await ledger.submit_request(pool_handle, schema_request.decode())
        raise Exception("Failed")
    except Exception as e:
        assert type(IndyError(ErrorCode.LedgerInvalidTransaction)) == type(e) and \
               IndyError(ErrorCode.LedgerInvalidTransaction).args == e.args


@pytest.mark.asyncio
async def test_schema_requests_works(pool_handle, wallet_handle):
    (trustee_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                               '{"seed":"000000000000000000000000Trustee1"}')
    (my_did, my_ver_key, _) = await signus.create_and_store_my_did(wallet_handle,
                                                                   '{"seed":"00000000000000000000000000000My1"}')

    schema_data = {
        "name": "gvt2",
        "version": "2.0",
        "keys": ["name", "male"]
    }

    nym_request = await ledger.build_nym_request(trustee_did.decode(), my_did.decode(), my_ver_key.decode(), None, None)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did.decode(), nym_request.decode())
    schema_request = await ledger.build_schema_request(my_did.decode(), json.dumps(schema_data))
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, my_did.decode(), schema_request.decode())
    get_schema_data = {
        "name": "gvt2",
        "version": "2.0"
    }
    get_schema_request = await ledger.build_get_schema_request(my_did.decode(), my_did.decode(), json.dumps(get_schema_data))
    response = json.loads((await ledger.submit_request(pool_handle, get_schema_request.decode())).decode())
    assert response['result']['data'] is not None


@pytest.mark.asyncio
async def test_send_node_request_works_without_signature(pool_handle, wallet_handle):
    (my_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                          '{"seed":"00000000000000000000000000000My1"}')

    node_data = {
        "node_ip": "10.0.0.100",
        "node_port": 9710,
        "client_ip": "10.0.0.100",
        "client_port": 9709,
        "alias": "Node5",
        "services": ["VALIDATOR"]
    }

    node_request = await ledger.build_node_request(my_did.decode(), my_did.decode(), json.dumps(node_data))

    try:
        await ledger.submit_request(pool_handle, node_request.decode())
        raise Exception("Failed")
    except Exception as e:
        assert type(IndyError(ErrorCode.LedgerInvalidTransaction)) == type(e) and \
               IndyError(ErrorCode.LedgerInvalidTransaction).args == e.args


@pytest.mark.asyncio
async def test_claim_def_requests_works(pool_handle, wallet_handle):
    (trustee_did, _, _) = await signus.create_and_store_my_did(wallet_handle,
                                                               '{"seed":"000000000000000000000000Trustee1"}')
    (my_did, my_ver_key, _) = await signus.create_and_store_my_did(wallet_handle,
                                                                   '{"seed":"00000000000000000000000000000My1"}')

    schema_data = {
        "name": "gvt2",
        "version": "2.0",
        "keys": ["name", "male"]
    }

    nym_request = await ledger.build_nym_request(trustee_did.decode(), my_did.decode(), my_ver_key.decode(), None, None)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did.decode(), nym_request.decode())

    schema_request = await ledger.build_schema_request(my_did.decode(), json.dumps(schema_data))
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, my_did.decode(), schema_request.decode())

    get_schema_data = {
        "name": "gvt2",
        "version": "2.0"
    }

    get_schema_request = await ledger.build_get_schema_request(my_did.decode(), my_did.decode(), json.dumps(get_schema_data))
    get_schema_response = json.loads((await ledger.submit_request(pool_handle, get_schema_request.decode())).decode())

    claim_def = {
        "primary": {
            "n": "83469852984476956871633111285697420678256060723156580163068122759469567425381600849138438902552107548539766861666590365174848381535291010418041757276710240953030842046122202402016906205924972182252295487319094577329593677544393592632224714613427822130473474379696616183721440743475053734247824037725487533789856061706740833324717788602268746116297029721621398888459529131593826880823126900285858832457134377949183677639585442886904844793608783831753240185678448312284269486845497720949217396146132958861735347072722092449280372574205841746312833280031873247525372459800132930201998084029506922484661426185450002143461",
            "s": "36598527821865478336201608644402887021319976830281254144922838415193047189326184120876650311572665920640111967758238425066565864958446810892401358531545590342401290056836149703549220109981509774843525259400920352082531560361277411808530872594109525982462491998670199872903823657869742599086495624835178373073050767142081484206776345277546531080450529061958937980460303537107061046725579009809137197541389237618812289642185603461102513124991949835948586623327143696280240600789928383168220919049794681181861776889681393339729944540218566460627715413465709316412838042632482652979005394086058441511591756153781159121227",
            "rms": "23836382972046033209463023456985914927629254782286444334728987813724281765327660893337383450653748691133061782449580026414785334582859397732571499366000805280757877601804441568263743400086744823885203441870748890135445454347495577599234477813361254101857848089907496868136222777024967328411073984887059985103475100012787049491016895625234124538894645853939428009610771524580099452739392988318945585946758355611531582519514003714424216836334706370901576611410508113637778751976890941210538254418937285168453791223070083264852447713991114719905171445881819334587600693321106919667204512182250084258986170095774914769107",
            "r": {
                "age": "15428480888651268593621235736458685943389726269437020388313417035842991073151072061010468945249435098482625869236498750525662874597991333642865524104221652457788998109101749530884821300954337535472137069380551054204373136155978715752232238326100335828797868667735730830741789880726890058203015780792583471770404478023662994191588489722949795849990796063953164194432710764145637578113087142419634074378464118254848566088943085760634805903735300398689750649630456000759025366784986694635635510206166144055869823907120081668956271923743188342071093889666111639924270726451727101864752767708690529389259470017692442002767",
                "name": "74008461204977705404956807338714891429397387365673402608947856456696416827848931951447004905350314563364442667940680669672331872875260077257474781261367591510351742401708951175978700805098470304211391452678992053755170054677498844656517106987419550598382601263743442309896367374279461481792679346472671426558385003925845431219156475505665973289508268634194964491418902859845301351562575713510002838692825728016254605821829245646855474149449192539144107522081712005891593405826343897070114168186645885993480245755494685105636168333649181939830898090651120926156152753918086493335382129839850609934233944397884745134858",
                "sex": "40646934914193532541511585946883243600955533193734077080129022860038019728021796610599139377923881754708640252789475144625086755150150612623804964347576907276705600241268266301487516824189453869193926251791711672689649199860304727280764676403810510047397326018392955950249975529169980045664874433828266623495515931483137318724210483205730962036282580749206735450480976847188040030165278917936054139926609849181885654646269083459580415131952938813839182742590617440550773580790446467896469090164142755499827316294406540664375065617280568303837662431668218593808092907551353093044984225946834165309588512359379032847125",
                "height": "60077310006190228182950362501472785016827894350517184186566050586806482282196022414888288252599211919680339352529750982779980002923071031258837648242708410943080288964834346858544959217874890558006056551949543916094446891954292824146212277550956558692224016968153138097595802008943263818064605343108607131298420107448075252583276684858815371561492996587478784667827675142382692061950832554910690663724101360454494298013020706080246986445114235542283015624510836206522238238728405826712730615187235709554561445384409566940622412591208469650855059870671771721035756205878334354791247751663679130847366069215369484993653"
            },
            "rctxt": "36378575722516953828830668112614685244571602424420162720244033008706985740860180373728219883172046821464173434592331868657297711725743060654773725561634332269874655603697872022630999786617840856366807034806938874090561725454026277048301648000835861491030368037108847175790943895107305383779598585532854170748970999977490244057635358075906501562932970296830906796719844887269636297064678777638050708353254894155336111384638276041851818109156194135995350001255928374102089400812445206030019103440866343736761861049159446083221399575945128480681798837648578166327164995640582517916904912672875184928940552983440410245037",
            "z": "65210811645114955910002482704691499297899796787292244564644467629838455625296674951468505972574512639263601600908664306008863647466643899294681985964775001929521624341158696866597713112430928402519124073453804861185882073381514901830347278653016300430179820703804228663001232136885036042101307423527913402600370741689559698469878576457899715687929448757963179899698951620405467976414716277505767979494596626867505828267832223147104774684678295400387894506425769550011471322118172087199519094477785389750318762521728398390891214426117908390767403438354009767291938975195751081032073309083309746656253788033721103313036"
        },
        "revocation": None
    }

    claim_def_request = await ledger.build_claim_def_txn(
        my_did.decode(), get_schema_response['result']['seqNo'], "CL", json.dumps(claim_def))

    await ledger.sign_and_submit_request(pool_handle, wallet_handle, my_did.decode(), claim_def_request.decode())
    get_claim_def_request = await ledger.build_get_claim_def_txn(
        my_did.decode(), get_schema_response['result']['seqNo'], "CL", get_schema_response['result']['data']['origin'])
    get_claim_def_response = json.loads(
        (await ledger.submit_request(pool_handle, get_claim_def_request.decode())).decode())
    assert claim_def == get_claim_def_response['result']['data']