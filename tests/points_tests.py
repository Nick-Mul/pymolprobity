import unittest

import mock

from .context import pymolprobity
import pymolprobity.points as pt


###############################################################################
#
#  CGO Utils
#
###############################################################################

class CgoColorTests(unittest.TestCase):
    @mock.patch('pymolprobity.points.cgo')
    @mock.patch('pymolprobity.points.colors.get_color_rgb')
    def test(self, mock_get_rgb, mock_cgo):
        mock_get_rgb.return_value = (1.0, 1.0, 1.0)
        mock_cgo.COLOR = 'COLOR'
        inp = 'white'
        ref = ['COLOR', 1.0, 1.0, 1.0]
        res = pt._cgo_color(inp)
        self.assertEqual(res, ref)


class CgoSphereTests(unittest.TestCase):
    @mock.patch('pymolprobity.points.cgo')
    def test(self, mock_cgo):
        mock_cgo.SPHERE = 'SPHERE'
        pos = (0.0, 1.0, 2.0)
        rad = 0.03
        ref = ['SPHERE', 0.0, 1.0, 2.0, 0.03]
        res = pt._cgo_sphere(pos, rad)
        self.assertEqual(res, ref)


class PerpVecTests(unittest.TestCase):
    def test_with_nonzero_first_coord(self):
        inp = (1, 0, 0)
        ref = [0, 1.0, 1.0]
        res = pt._perp_vec(inp)
        self.assertEqual(res, ref)

    def test_with_nonzero_second_coord(self):
        inp = (0, 1, 0)
        ref = [1.0, 0, 1.0]
        res = pt._perp_vec(inp)
        self.assertEqual(res, ref)

    def test_with_nonzero_third_coord(self):
        inp = (0, 0, 1)
        ref = [1.0, 1.0, 0]
        res = pt._perp_vec(inp)
        self.assertEqual(res, ref)

    def test_with_all_nonzero_coords(self):
        inp = (1, 1, 1)
        ref = [-2.0, 1.0, 1.0]
        res = pt._perp_vec(inp)
        self.assertEqual(res, ref)

class CgoQuadTests(unittest.TestCase):
    @mock.patch('pymolprobity.points.cpv')
    @mock.patch('pymolprobity.points.cgo')
    def test(self, mock_cgo, mock_cpv):
        mock_cgo.BEGIN = 'BEGIN'
        mock_cgo.TRIANGLE_STRIP = 'TRISTRIP'
        mock_cgo.NORMAL = 'NORMAL'
        mock_cgo.VERTEX = 'VERTEX'
        mock_cgo.END = 'END'
        mock_cpv.add.side_effect = [['v1'], ['v2']]
        mock_cpv.sub.side_effect = [['v3'], ['v4']]
        pos = (0, 1, 2)
        normal = (3, 4, 5)
        radius = 0.03
        ref = ['BEGIN', 'TRISTRIP', 'NORMAL', 3, 4, 5, 'VERTEX', 'v1',
                'VERTEX', 'v2', 'VERTEX', 'v3', 'VERTEX', 'v4', 'END']
        res = pt._cgo_quad(pos, normal, radius)
        self.assertEqual(res, ref)

class CgoCylinderTests(unittest.TestCase):
    @mock.patch('pymolprobity.points.cgo')
    def test(self, mock_cgo):
        mock_cgo.CYLINDER = 'CYLINDER'
        p1 = (0, 1, 2)
        p2 = (3, 4, 5)
        rad = 0.02
        c1 = (0, 0, 0)
        c2 = (1, 1, 1)
        ref = ['CYLINDER', 0, 1, 2, 3, 4, 5, 0.02, 0, 0, 0, 1, 1, 1]
        res = pt._cgo_cylinder(p1, p2, rad, c1, c2)
        self.assertEqual(res, ref)


###############################################################################
#
#  DOTLISTS
#
###############################################################################

class ProcessDotlistTests(unittest.TestCase):
    def setUp(self):
        self.base_context = {
                'kinemage': None,
                'group': None,
                'subgroup': None,
                'animate': 0,
            }

    @mock.patch('pymolprobity.points._parse_dotlist_body')
    @mock.patch('pymolprobity.points._parse_dotlist_header')
    def test_workflow(self, mock_parse_header, mock_parse_body):
        mock_parse_header.return_value = ('name', 'color', 'master')
        mock_parse_body.return_value = [pt.Dot(), pt.Dot(), pt.Dot()]
        inp = ['dotlist blah', 'line 1', 'line 2', 'line 3']
        res = pt.process_dotlist(inp, self.base_context)
        mock_parse_header.assert_called_once_with(inp[0])
        mock_parse_body.assert_called_once_with(inp[1:])
        for dot in res:
            self.assertEqual(dot.dotlist_name, 'name')
            self.assertEqual(dot.dotlist_color, 'color')
            self.assertEqual(dot.master, 'master')
            self.assertEqual(dot.kinemage, self.base_context['kinemage'])
            self.assertEqual(dot.group, self.base_context['group'])
            self.assertEqual(dot.subgroup, self.base_context['subgroup'])
            self.assertEqual(dot.animate, self.base_context['animate'])



class ParseDotlistHeaderTests(unittest.TestCase):
    def test1(self):
        inp = 'dotlist {x} color=white master={vdw contact}'
        ref = ('x', 'white', 'vdw_contact')
        res = pt._parse_dotlist_header(inp)
        self.assertEqual(res, ref)

    def test2(self):
        inp = 'dotlist {x} color=red master={H-bonds}'
        ref = ('x', 'red', 'H_bonds')
        res = pt._parse_dotlist_header(inp)
        self.assertEqual(res, ref)


@mock.patch('pymolprobity.points.colors.get_pymol_color')
class ParseDotlistBodyTests(unittest.TestCase):
    def test_general_form(self, mock_get_color):
        mock_get_color.return_value = 'colorname'
        inp = ["{AAAABCCCDDDDEFF}colorname  'G' 0.0,1.0,2.0"]
        ref_atom = {'name': 'AAAA',
                'alt': 'B',
                'resn': 'CCC',
                'resi': 'DDDDE',
                'chain': 'FF'}
        res = pt._parse_dotlist_body(inp)
        self.assertEqual(res[0].atom, ref_atom)
        self.assertEqual(res[0].color, 'colorname')
        self.assertEqual(res[0].pm, 'G')
        self.assertEqual(res[0].coords, [0.0, 1.0, 2.0])

    def test_with_spaces_in_atom_desc(self, mock_get_color):
        '''Should handle spaces in atom name, alt, resn, resi, and chain.'''
        mock_get_color.return_value = 'colorname'
        inp = ["{ CA  SER  26  A}colorname  'G' 0.0,1.0,2.0"]
        ref_atom = {'name': 'CA',
                'alt': '',
                'resn': 'SER',
                'resi': '26',
                'chain': 'A'}
        res = pt._parse_dotlist_body(inp)
        self.assertEqual(res[0].atom, ref_atom)

    def test_with_question_mark_in_atom_desc(self, mock_get_color):
        '''Should handle ? in atom name e.g. "H?" for water hydrogen.'''
        mock_get_color.return_value = 'colorname'
        inp = ["{ H?  HOH 293  A}colorname  'G' 0.0,1.0,2.0"]
        ref_atom = {'name': 'H',
                'alt': '',
                'resn': 'HOH',
                'resi': '293',
                'chain': 'A'}
        res = pt._parse_dotlist_body(inp)
        self.assertEqual(res[0].atom, ref_atom)

    def test_with_negative_coords(self, mock_get_color):
        '''Handle negative coordinates.'''
        mock_get_color.return_value = 'colorname'
        inp = ["{AAAABCCCDDDDEFF}colorname  'G' -0.0,-1.0,-2.0"]
        res = pt._parse_dotlist_body(inp)
        self.assertEqual(res[0].coords, [-0.0, -1.0, -2.0])

    def test_with_quotation_mark_atom(self, mock_get_color):
        '''Handle repeated atoms indicated by `{"}`.'''
        mock_get_color.return_value = 'colorname'
        inp = ['''{AAAABCCCDDDDEFF}colorname  'G' 0.0,1.0,2.0''',
               '''{"}colorname  'G' -0.0,-1.0,-2.0''']
        res = pt._parse_dotlist_body(inp)
        self.assertEqual(res[0].atom, res[1].atom)


###############################################################################
#
#  VECTORLISTS
#
###############################################################################

class ProcessVectorlistTests(unittest.TestCase):
    def setUp(self):
        self.base_context = {
                'kinemage': None,
                'group': None,
                'subgroup': None,
                'animate': 0,
            }

    @mock.patch('pymolprobity.points._parse_clash_vectorlist_body')
    @mock.patch('pymolprobity.points._parse_vectorlist_header')
    def test_workflow_with_clash_vectorlist(self, mock_parse_header,
            mock_parse_body):
        mock_parse_header.return_value = ('x', 'color', 'master')
        mock_parse_body.return_value = [pt.Vector(), pt.Vector(), pt.Vector()]
        inp = ['vectorlist blah', 'line 1', 'line 2', 'line 3']
        res = pt.process_vectorlist(inp, self.base_context)
        mock_parse_header.assert_called_once_with(inp[0])
        mock_parse_body.assert_called_once_with(inp[1:])
        for v in res:
            self.assertEqual(v.vectorlist_name, 'x')
            self.assertEqual(v.vectorlist_color, 'color')
            self.assertEqual(v.master, 'master')
            self.assertEqual(v.kinemage, self.base_context['kinemage'])
            self.assertEqual(v.group, self.base_context['group'])
            self.assertEqual(v.subgroup, self.base_context['subgroup'])
            self.assertEqual(v.animate, self.base_context['animate'])


    @mock.patch('pymolprobity.points._parse_bonds_vectorlist_body')
    @mock.patch('pymolprobity.points._parse_vectorlist_header')
    def test_workflow_with_bonds_vectorlist(self, mock_parse_header,
            mock_parse_body):
        mock_parse_header.return_value = ('mc', 'color', 'master')
        mock_parse_body.return_value = [pt.Vector(), pt.Vector(), pt.Vector()]
        inp = ['vectorlist blah', 'line 1', 'line 2', 'line 3']
        res = pt.process_vectorlist(inp, self.base_context)
        mock_parse_header.assert_called_once_with(inp[0])
        mock_parse_body.assert_called_once_with(inp[1:])
        for v in res:
            self.assertEqual(v.vectorlist_name, 'mc')
            self.assertEqual(v.vectorlist_color, 'color')
            self.assertEqual(v.master, 'master')
            self.assertEqual(v.kinemage, self.base_context['kinemage'])
            self.assertEqual(v.group, self.base_context['group'])
            self.assertEqual(v.subgroup, self.base_context['subgroup'])
            self.assertEqual(v.animate, self.base_context['animate'])


class ParseVectorlistHeaderTests(unittest.TestCase):
    def test_general_form(self):
        inp = 'vectorlist {x} color=foo master={bar}'
        ref = ('x', 'foo', 'bar')
        res = pt._parse_vectorlist_header(inp)
        self.assertEqual(res, ref)


@mock.patch('pymolprobity.points.colors.get_pymol_color')
class ParseClashVectorlistBodyTests(unittest.TestCase):
    def test_clash_general_form(self, mock_get_color):
        mock_get_color.return_value = 'somecolor'
        inp = ['''{AAAABCCCDDDDEFF}somecolor P  'O' 0.0,1.0,2.0 {"}somecolor   'O' 3.0,4.0,5.0''']
        ref_atom = {'name': 'AAAA',
                'alt': 'B',
                'resn': 'CCC',
                'resi': 'DDDDE',
                'chain': 'FF'}
        res = pt._parse_clash_vectorlist_body(inp)
        self.assertEqual(res[0].atom, [ref_atom, ref_atom])
        self.assertEqual(res[0].color, ['somecolor', 'somecolor'])
        self.assertEqual(res[0].pm, ['O', 'O'])
        self.assertEqual(res[0].coords, [[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]] )


    def test_with_spaces_in_atom_desc(self, mock_get_color):
        mock_get_color.return_value = 'colorname'
        inp = ['''{ CA  SER  26  A}somecolor P  'O' 0.0,1.0,2.0 {"}somecolor   'O' 3.0,4.0,5.0''']
        ref_atom = {'name': 'CA',
                'alt': '',
                'resn': 'SER',
                'resi': '26',
                'chain': 'A'}
        res = pt._parse_clash_vectorlist_body(inp)
        self.assertEqual(res[0].atom, [ref_atom, ref_atom])

    def test_with_question_mark_in_atom_desc(self, mock_get_color):
        '''Should handle ? in atom name e.g. "H?" for water hydrogen.'''
        mock_get_color.return_value = 'colorname'
        inp = ['''{ H?  HOH 293  A}somecolor P  'O' 0.0,1.0,2.0 {"}somecolor   'O' 3.0,4.0,5.0''']
        ref_atom = {'name': 'H',
                'alt': '',
                'resn': 'HOH',
                'resi': '293',
                'chain': 'A'}
        res = pt._parse_clash_vectorlist_body(inp)
        self.assertEqual(res[0].atom, [ref_atom, ref_atom])

    def test_with_negative_coords(self, mock_get_color):
        '''Handle negative coordinates.'''
        mock_get_color.return_value = 'colorname'
        inp = ['''{AAAABCCCDDDDEFF}somecolor P  'O' -0.0,-1.0,-2.0 {"}somecolor   'O' -3.0,-4.0,-5.0''']
        res = pt._parse_clash_vectorlist_body(inp)
        self.assertEqual(res[0].coords, [[-0.0, -1.0, -2.0], [-3.0, -4.0, -5.0]])


class ParseBondsVectorlistBody(unittest.TestCase):
    def test_bond_vector_general_form(self):
        inp = ['''{AAAABCCCFFDDDDE B12.34 objFH} P 'O' 0.0,1.0,2.0 {GGGGHIIILLJJJJK B56.78 objFH} P 'O' 3.0,4.0,5.0''']
        ref_atom1 = {'name': 'AAAA',
                'alt': 'B',
                'resn': 'CCC',
                'resi': 'DDDDE',
                'chain': 'FF',
                'occ': 1.0,
                'b': 12.34}
        ref_atom2 = {'name': 'GGGG',
                'alt': 'H',
                'resn': 'III',
                'resi': 'JJJJK',
                'chain': 'LL',
                'occ': 1.0,
                'b': 56.78}
        res = pt._parse_bonds_vectorlist_body(inp)
        self.assertEqual(res[0].atom, [ref_atom1, ref_atom2])
        self.assertEqual(res[0].color, [None, None])
        self.assertEqual(res[0].pm, ['O', 'O'])
        self.assertEqual(res[0].coords, [[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]] )

    def test_with_continuous_bonds_carryover_second_atom(self):
        inp = ['''{AAAABCCCFFDDDDE B12.34 objFH} P 'O' 0.0,1.0,2.0 {GGGGHIIILLJJJJK B56.78 objFH} P 'O' 3.0,4.0,5.0''',
               '''{MMMMNOOORRPPPPQ B9.10 objFH} P 'O' 0.0,1.0,2.0 ''']
        res = pt._parse_bonds_vectorlist_body(inp)
        ref_atom1 = {'name': 'AAAA',
                'alt': 'B',
                'resn': 'CCC',
                'resi': 'DDDDE',
                'chain': 'FF',
                'occ': 1.0,
                'b': 12.34 }
        ref_atom2 = {'name': 'GGGG',
                'alt': 'H',
                'resn': 'III',
                'resi': 'JJJJK',
                'chain': 'LL',
                'occ': 1.0,
                'b': 56.78 }
        ref_atom3 = {'name': 'MMMM',
                'alt': 'N',
                'resn': 'OOO',
                'resi': 'PPPPQ',
                'chain': 'RR',
                'occ': 1.0,
                'b': 9.10 }
        print res[1].atom
        print ref_atom2
        print ref_atom3
        self.assertEqual(res[0].atom, [ref_atom1, ref_atom2])
        self.assertEqual(res[1].atom, [ref_atom2, ref_atom3])

    def test_with_partial_occupancy(self):
        inp = ['''{AAAABCCCFFDDDDE 0.50 B12.34 objFH} P 'O' 0.0,1.0,2.0 {GGGGHIIILLJJJJK 0.50 B56.78 objFH} P 'O' 3.0,4.0,5.0''']
        res = pt._parse_bonds_vectorlist_body(inp)
        self.assertEqual(res[0].atom[0]['occ'], 0.50)
        self.assertEqual(res[0].atom[1]['occ'], 0.50)

    def test_raises_indexerror_when_first_line_has_only_one_point(self):
        inp = ['''{AAAABCCCFFDDDDE 0.50 B12.34 objFH} P 'O' 0.0,1.0,2.0''']
        with self.assertRaises(IndexError):
            pt._parse_bonds_vectorlist_body(inp)

    def test_raises_valueerror_with_zero_matches(self):
        inp = ['''not a match''']
        with self.assertRaises(ValueError):
            pt._parse_bonds_vectorlist_body(inp)

    def test_raises_valueerror_with_more_than_2_matches(self):
        inp = ['''{AAAABCCCFFDDDDE 0.50 B12.34 objFH} P 'O' 0.0,1.0,2.0 {AAAABCCCFFDDDDE 0.50 B12.34 objFH} P 'O' 0.0,1.0,2.0 {GGGGHIIILLJJJJK 0.50 B56.78 objFH} P 'O' 3.0,4.0,5.0''']
        with self.assertRaises(ValueError):
            pt._parse_bonds_vectorlist_body(inp)







class DotTests(unittest.TestCase):
    @mock.patch('pymolprobity.points.colors.get_pymol_color')
    def test_init(self, mock_get_color):
        mock_get_color.return_value = 'somecolor'
        d = pt.Dot()
        self.assertEqual(d.atom, None)
        self.assertEqual(d.color, 'somecolor')
        self.assertEqual(d.pm, None)
        self.assertEqual(d.coords, None)
        self.assertEqual(d.draw, 1)
        self.assertEqual(d.dotlist_name, None)
        self.assertEqual(d.dotlist_color, None)
        self.assertEqual(d.master, None)

    @mock.patch('pymolprobity.points._cgo_sphere')
    @mock.patch('pymolprobity.points._cgo_color')
    def test_get_cgo_workflow_with_defaults(self, mock_color, mock_sphere):
        mock_color.return_value = ['color']
        mock_sphere.return_value = ['sphere']
        d = pt.Dot()
        d.color = 'white'
        d.coords = (0.0, 1.0, 2.0)

        res = d.get_cgo()
        ref = ['color', 'sphere']
        self.assertEqual(res, ref)

        mock_color.assert_called_once_with('white')
        mock_sphere.assert_called_once_with((0, 1, 2), 0.03)

    @mock.patch('pymolprobity.points.cpv')
    @mock.patch('pymolprobity.points._cgo_quad')
    @mock.patch('pymolprobity.points._cgo_color')
    def test_get_cgo_with_dot_mode_1(self, mock_color, mock_quad, mock_cpv):
        mock_color.return_value = ['color']
        mock_quad.return_value = ['quad']
        mock_cpv.normalize.return_value = (1, 0, 0)
        d = pt.Dot()
        d.color = 'white'
        d.coords = (0.0, 1.0, 2.0)
        d.atom = {'coords': (3.0, 4.0, 5.0)}

        res = d.get_cgo(dot_mode=1)

        ref = ['color', 'quad']
        self.assertEqual(res, ref)

        mock_color.assert_called_once_with('white')
        mock_quad.assert_called_once_with((0.0, 1.0, 2.0), (1, 0, 0), 0.03 *
                1.5)
        mock_cpv.sub.assert_called_once_with((0.0, 1.0, 2.0), (3.0, 4.0, 5.0))



class VectorTests(unittest.TestCase):
    @mock.patch('pymolprobity.points.colors.get_pymol_color')
    def test_init(self, mock_get_color):
        mock_get_color.return_value = None
        v = pt.Vector()
        self.assertEqual(v.atom, [None, None])
        self.assertEqual(v.color, [None, None])
        self.assertEqual(v.pm, [None, None])
        self.assertEqual(v.coords, [None, None])
        self.assertEqual(v.draw, 1)
        self.assertEqual(v.vectorlist_name, None)
        self.assertEqual(v.vectorlist_color, None)
        self.assertEqual(v.master, None)

    @mock.patch('pymolprobity.points._cgo_sphere')
    @mock.patch('pymolprobity.points._cgo_color')
    @mock.patch('pymolprobity.points._cgo_cylinder')
    @mock.patch('pymolprobity.points.colors.get_color_rgb')
    def test_get_cgo_workflow_with_defaults(self, mock_get_rgb, mock_cylinder,
            mock_color, mock_sphere):
        mock_get_rgb.return_value = 'rgb'
        mock_cylinder.return_value = ['cylinder']
        mock_color.return_value = ['color']
        mock_sphere.return_value = ['sphere']

        v = pt.Vector()
        v.color = ['white', 'white']
        v.coords = [(0.0, 1.0, 2.0), (3.0, 4.0, 5.0)]

        res = v.get_cgo()
        ref = ['cylinder', 'color', 'sphere', 'color', 'sphere']
        self.assertEqual(res, ref)

        mock_color.assert_has_calls([mock.call('white'), mock.call('white')])
        cyl_args = [(0.0, 1.0, 2.0), (3.0, 4.0, 5.0), 0.03, 'rgb', 'rgb']
        mock_cylinder.assert_called_once_with(*cyl_args)
        mock_sphere.assert_has_calls([mock.call( (0.0, 1.0, 2.0), 0.03 ),
                                      mock.call( (3.0, 4.0, 5.0), 0.03 )])

    @mock.patch('pymolprobity.points.cpv')
    @mock.patch('pymolprobity.points._cgo_quad')
    @mock.patch('pymolprobity.points._cgo_color')
    def test_get_cgo_with_dot_mode_1(self, mock_color, mock_quad, mock_cpv):
        mock_color.return_value = ['color']
        mock_quad.return_value = ['quad']
        mock_cpv.normalize.return_value = (1, 0, 0)
        d = pt.Dot()
        d.color = 'white'
        d.coords = (0.0, 1.0, 2.0)
        d.atom = {'coords': (3.0, 4.0, 5.0)}

        res = d.get_cgo(dot_mode=1)

        ref = ['color', 'quad']
        self.assertEqual(res, ref)

        mock_color.assert_called_once_with('white')
        mock_quad.assert_called_once_with((0.0, 1.0, 2.0), (1, 0, 0), 0.03 *
                1.5)
        mock_cpv.sub.assert_called_once_with((0.0, 1.0, 2.0), (3.0, 4.0, 5.0))



if __name__ == '__main__':
    unittest.main()







