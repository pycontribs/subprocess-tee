# spell-checker:ignore bcond pkgversion buildrequires autosetup PYTHONPATH noarch buildroot bindir sitelib numprocesses clib
# All tests require Internet access
# to test in mock use:  --enable-network --with check
# to test in a privileged environment use:
#   --with check --with privileged_tests
%bcond_with     check
%bcond_with     privileged_tests

Name:           subprocess-tee
Version:        VERSION_PLACEHOLDER
Release:        1%{?dist}
Summary:        subprocess-tee

License:        MIT
URL:            https://github.com/pycontribs/subprocess-tee
Source0:        %{pypi_source}

BuildArch:      noarch

BuildRequires:  pyproject-rpm-macros
BuildRequires:  python%{python3_pkgversion}-build
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-setuptools_scm
BuildRequires:  python%{python3_pkgversion}-wheel
%if %{with check}
# These are required for tests:
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-pytest-xdist
BuildRequires:  git
%endif

# generate_buildrequires
# pyproject_buildrequires

%description
setuptools-scm

%prep
%autosetup


%build
%pyproject_wheel


%install
%pyproject_install


%if %{with check}
%check
PYTHONPATH=%{buildroot}%{python3_sitelib} \
  pytest-3 \
  -v \
  --disable-pytest-warnings \
  --numprocesses=auto \
%if %{with privileged_tests}
  tests
%else
  tests/unit
%endif
%endif


%files
%{python3_sitelib}/subprocess_tee/
%{python3_sitelib}/subprocess_tee-*.dist-info/
%license LICENSE
%doc * README.md

%changelog
Available at https://github.com/pycontribs/subprocess-tee/releases
