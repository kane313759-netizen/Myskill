"""r4-3.6 regression: (1) a rejection/zero-score condition with unclear reach is not dismissed by source difference -> common answer,
(2) broken records or sample-different formats are quarantined instead of rejecting the whole bundle, (3) the one-sided 95% upper end
comes from the measured error distribution, not the historical maximum. Prior (r4-3.5) SKILL lines intact."""
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
PRIOR_LINE_HASHES = (
    'cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b',
    '930627ac417b9f49b610375e511830d8a77268528c2fc16df610ca849a97d196',
    # 'abe27c14b1a82a3e612f848e66c84be068d904df46ede31d1344f841ba403dad',  # SKILL description line: replaced in r4-3.10 (entry-point description)
    '99b8c61790ede3032957d09a7046cca3f61d54668c24ef2eefc319259119d6a3',
    '2fae26f95db4c26ba45129e12b09e456618b9e2474256f129cab8420820740f7',
    '1f19c338390c4d36ad27f273959e7d3b4bab02a8a28719f383f9466b7b4616b1',
    '0f2d816023e7570bc4a4ee845f000f4c7585b8d1e8c1099a6703e951d9650d01',
    '85c8f4b5d0d68b444759d75b959d896ad4b9a5e479a1fddc500e4208d3a01a4d',
    '7098d75080669d8466e83027129bad82f9d46b0130f7aae03b9e577a3640dcc0',
    '7a0dfde5a4fe027f8b734f80e1bb874bf857ceb05732d566622cadb58cd3c6f5',
    '5240b4eb22f00f3fc7b6f08ce37e8a3ee4c8b7f20a8ba8ffd04f74af71924814',
    '9e79c2c6a595782c6ad7cb2e7e11ede513a7b8d4bdfd1d97a5840b7116c25bf1',
    '48f68a244fdd7cd791a78fd3d8383ab3382372bccfe2e2ff413baabe91e6b110',
    '339b327f02eecc4eef4120941739fb14e8aa389749fa2d74bfa5d98e124c7c7d',
    '1462e8f72ac16c03c97f328533b9412dcfa615c0a38fd794a32138ddecb135dc',
    '4ae7059824561f9e387a161fd5a9c049b6eec11fad7825ee3e6d1b0af6593477',
    '35633ca3d9b80a153ec6de2ba4f2123dd56490432d2f759eab56e0f102a80d5c',
    'e876e2f64662b55adc6f0ee5f204a0a5a959bc01476148e0e035133b549dd090',
    'a0693b7ed99ae9e79ae47059b3986a06de64a6bd37d67e7c4fcfa3a9955bff8f',
    '62f94bdcc5f045675a92f56eeeda237afe8211e8d59e26bd72a09ee16c718c70',
    '2d8ebe49608e0bec4c7f2d93f96d53093c2dad8343285898283728e3dea813d9',
    '9b9cc8aa8a886b9ff11fcdee1d749731a7777c0f049d6b637ca8375ff0a9626f',
    '5351a4beae6f470a5e3b61111e09d5f807f334069ad3cdb132cf8de0598766b9',
    'f403e065b0e2d6e37814f6aa20a6779d6ea32581386296d3554e605a94e63148',
    '59952e7246f6b36d0b7e7ac4d299cfadfec12f0f526c86071e537c2de6b957db',
    '0e6913e4de7e843615dc0dfd9ca8370d5a2819aa41a5a1c79ab7e953fafc52a8',
    '950782ba5c163b187bfc4623adb645833801a2d89afd5dba1862f96fb92c57e8',
    'c6f3a13901946a3c7f04a864a6d34558de7252a2fa5e2038a13aa3f55d2994e8',
    '849fa4c12f1f9c80315acb732b6633faa786b25fc0cf25d78930bfef802a5765',
    '759362a6032ccfe396abbb9d1d8abfd083d83ad21b4b46db4a0d34d27d31a96c',
    'a2723c14e5120fb88426f0ae49809b8186ec5d96b52a59b44ae1be11bb584254',
    'fe26203904fa427d7ab8ac51c12d1a40155f5663f15ee4c12cc3e887a97a1fd1',
    'e638c065718f76f69c8c32f235b04297fdc939d0093410a3385797d573f208e7',
    '28d2a92fb47e8be9bf6d9af9a352ec50e65244d3cb97f62469ad1c492d265eb4',
    '37e91e7a117892a0aa048ea1ed47b10f60b6c23cbacbe6b446ddbed89ce20eea',
    '7b976b1665509502d69191cee2c093679dd7fcfe9395426a9091b9ddf9e6cdf4',
    '92860d1631f3d1f783b3d98419208c4e937b7bf818bcb0d9797308f12f5155d4',
    'd12b66a6dcce26c3a660ca3cfa51ca683e37e1c1b406bcbd3432f962b7ec6a18',
    '1785999cf2d95932300885959ae55ed8f5df702549c6d76eafd9697113e195e0',
    'd538a24905c8095b450817a203a5d5c38897795b76ad5098b8eecd6bf7702ef2',
    '4ca6e8e8cbb046cf70d1d423f444f0a5b6c28814165ebf638936f79f9c5a7fe6',
    'c25a2822357a09d38af1b653fe9bb3e34e45f59a97ce398b4d7efd1c6341c176',
    '5d6ef3d272fa2ccb8c1b9aa84db12fe1d17b83935d61be151cab0972f8ceaefd',
    '6ee15907d4580856d28e967c1e63344cd3970af32a9e3b81f50787cc5166e85c',
    '6600b29c7bde7bf543003663c134b9782d0d669140c3b7398e886a97085b0e0d',
    'aa76f3acdf2784d5312258df9bf47de17d030e8ebc71c7d47357396194167cba',
    '8658384fa261a36f4f010fcb3995d8c4f454660173ee57cd0646058e96e5ae40',
    'b30e6637432976a4d998b023e3610c6885bb2a9cb8bc7925e929cf2556b134f4',
    'beb684e0474aec20a6efc0aeba302135e932455314dda56532648e9cccaa3d75',
    'aae41834db8388a544216ab90a914509cb19aa4d25fde2966f6f8174db41c41f',
    '6f69062bfb2eba2b3e7b10e99c991c6b93efd537f82728c9583ba5508092fa39',
    '4c891d1ce3dff6eb71e9a4f370203e4105c59466aa0de2e205bec82c1f4c1ab0',
    'af3b2fcb1f32ee7e71d50db2d735a786c818fb9b896fd13a2550b1f4b4577012',
    '09fa3dcbdc0cd9fdbb656d715e6669d0fdd33335f0681101e6eb2d73d534a186',
    '7d2425b54cfcea87622e17a5bee4b645102690a41020b319f7f42f2548cb4561',
    'e104bd25a079c967230d7b2947864e1dbf371892b67d742925b4d301cb2ced9d',
    '7bc2af5dce7e45acde798a7fac316069b8047ed6ae670269956f7d2c2838477a',
    '388fedca2f74078ff522d315f6af6d994419055890b18a2c3469df87754f6020',
    '6eb7529e7d5ff031d693f86d41b1a6458187b6f0f1c49330575ce71a24e6d994',
    '3a19b24fa55e00615e225c180b6293d5ad8c739bb4fcd28fbdc61b3625179932',
    '3409d6c737868bc9724fe50e0111e6609f9cb094e89e4a849f9a911a797d989b',
    '0f0c8b35878c777d4d1bd631074999c0cd6c5243f812c4895437abf200b360f6',
    'e4039790ad0eb859c4ef154919da0ce564cc982ce45314d3e284d6252f15fedd',
    'a2b5ded7a54e57967d6857c029369c6f4088368ade5db15c8c8916310b844820',
    'd1ff9ef5839bb4e4f6c3a7623cdde7af5adc06a5d414a5dd5c980b68070cd5c1',
    'ca36e92b43526d4d06e45b2a523d32ed11bbb3ba33af5c42d3fef940e92fdd86',
    'a49f19123d281be452436886cdc77a391121b8014b1b8ba694e9707c041314e4',
    '218f43a765b946c3e183cba3b9cb987bfd9fd40d0f1fd17e33242a5880e4e401',
    '827873f9f70acb6642c6571a5627b65cba21826d5e7257187842a08d2ffa8812',
    '7c5c135f4c8466071bf809e17c16fe314030b05866d55212af151f3ec8e22246',
    '7a13eaf88d769cb63a6e5b4c849674a0b7d11b85bfabae5b66f32a6a9f233a19',
    '2e506338bb0be39fb3c2c6f9d73511c524b44389180635751c568f255d38a6a5',
    '5ab38b57a3d81029cf0e822512df7cff8f093d8991c6125cadbdeb0cb0ce50bd',
    'f1df2f8133eda34c0a8e9fec3d19ea288a8f7277f99a2e047e5b18fcc78dfb42',
    '0c725ad6969a7ff4e1ac87cd0ec186d25123eb002ce9acd5e0f5ad5ee8db43f6',
    '4d7b36329069f2bd4cfec0c6146a04e0eef52625a2b9a4a2c72200eaefa18cf7',
    '716b1dfec6e919fd45ca7a8f3d00b53054571015e683f32012c2ee29b6cb3b77',
    'eb13b147ba2a2b9e984b0ffddfa4688cde532f56f085f7704774e6f8206c6d2e',
    'ac3e4fb6fc903b7354fefd2151ee5dc68f68f30acd92ad06b3a2e85a2e7d93da',
    '978e2260abd59795ffe264d745d94a4be38ccb928bbac77447e71588865f7b04',
    '9a60c8626b522517c50c03e37642f5ccca874924884dd7e44df73c17bf5d4102',
    'd994e23a185286b676a6a03988686ef91a1f217b23bfebcc12f1068a9561901d',
    '9acb5fc84fb9a2a2f8feac08755eac1d88229bf467360d0b0fa49b89bf2f13bc',
    'f959b8ffea460771e87a43b9982f9d814f96221ed5f0f891d848d2ffe20275a0',
    'd27844659f8aa3cdfc45321df770e4b3d0398bfc6cda468e0bc10b95195ae29a',
    'dd6aa87f85c6442338d67560c36bf652b7e232feec8f4836fccc9f351433228c',
    '3c4e9cb2252662b8f08a31b5c02477eed218ec44db53465fb8b417675d90aa1b',
    '637abf22bb8ce3a59e4833128951a62bedfd2e243128ee5e7b3eb63c29e30f4d',
    '01b6140a0f94208732a6fabe25a41fd1a503c378df4a7c0d11f767197b4a7da6',
    'b4fe1c2ef37685b74805a33ee80cac5e369fbbed3858fbdfae0a4cc2e4330b95',
    '84a0edf5614107e37bc4f34cdc67b913850259d2f74167973a89a9a590706f49',
    'f47e2cc234c13b435fcb495b44d84c9f1fbb297bd10ce5d64dfe8a0196393f07',
    '02c6fa975afaf72bb1812527f8a0094eb09200fa13c4c24a8caa40152a9f05e5',
    '00b6ade81261cf2bfbd7e4d50749e2abb0dfecdeac63aa8090cc331437bb620a',
    'ef9f89f600ab988beba46b964dd64846b540ddc01fd989f0f6c505b47f743cad',
    'e8247dd9b05b26df3df9f3e96219f64d164ec0e6b6baac3bf1e0825b3ac9705a',
    'd26c899e5331433917c567fc8f1774a33742d45de094897aa803d1775f7fb7f3',
    '6bf9dc0c37a00597a2c660fbe935eadc9ad57f5dfb841a4da3a2474189ab3f06',
    '65e2a2c1810af14b9bdc4982c27a0a8e8486899a0cf2fba78efd3099e33762ce',
    '5954633a73826ea10f31b097be54b71806915f61e1dafb58503b51983ebc24ae',
    '2866a8e555ebc1c30adf5e94a82c80c247ea5caf86ae390f69e530ff0c8f804a',
    'e1b1034f27206d917a4f334309c64f65071ed63df744ae76149275c96a2838da',
    '6a7e20882845917a1232218a62ff74dbaa45b01df5db791d27f10599a2a12283',
    '3a54256d7fafb8a9aafb4ade6b999380c4025bf755600da08a87a4e8b7017059',
)
TERMS = ('반려·0점·실격이 걸린 조건', '출처나 집계 경로가 다르다는 이유만으로 해당 없음으로 정하지 않는다', '그 조건을 피하는 공통안',
         '그 기록만 격리하고 사유를 남긴 뒤 나머지를 처리한다', '과제 문서가 정한 거부 조건', '깨진 행 하나와 형식이 다른 칸 하나를 넣은 묶음',
         '잰 오차의 분포에서 구한다', '이력의 최대 오차(최악 사례)')


class RegressionR436(unittest.TestCase):
    def test_01_document_guard(self):
        text = (ROOT / SKILL).read_text(encoding='utf-8')
        for term in TERMS:
            self.assertIn(term, text)
        present = {hashlib.sha256(line.encode('utf-8')).hexdigest() for line in text.splitlines()}
        self.assertEqual([h for h in PRIOR_LINE_HASHES if h not in present], [], 'r4-3.5 SKILL lines removed or changed')
        self.assertIn('## r4-3.6', (ROOT / 'references/v27-contract.md').read_text(encoding='utf-8'))

    def test_02_rule_order(self):
        lines = (ROOT / SKILL).read_text(encoding='utf-8').splitlines()
        idx = lambda s: next(i for i, l in enumerate(lines) if s in l)
        self.assertEqual(idx('반려·0점·실격이 걸린 조건'), idx('주최 측·업무 담당자의 답이 끝내 없거나') + 1)
        self.assertEqual(idx('그 기록만 격리하고'), idx('산출물이 시스템·에이전트·정책이면') + 1)
        self.assertEqual(idx('잰 오차의 분포에서 구한다'), idx('과제 한도(불량률·이탈률 등)를 추정값으로') + 1)

    def test_03_protected_files(self):
        files = json.loads((ROOT / 'references/v27-baseline.json').read_text(encoding='utf-8'))['files']
        self.assertEqual(len(files), 112)
        for path, digest in files.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)


if __name__ == '__main__':
    unittest.main()
